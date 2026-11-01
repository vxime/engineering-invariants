/**
 * First-party synthetic MCP-like response classifier. Offline loopback only.
 * Node.js 22; no MCP SDK, Cakewalk runtime, credentials or external network.
 * 2026-07-28 base-protocol compatibility: missing resultType is "complete".
 * This deliberately omits real MCP negotiation, _meta, authorization and MRTR.
 * Run: node --test --test-reporter=tap mcp-error-layers-v3.test.mjs
 */
import assert from 'node:assert/strict';
import { once } from 'node:events';
import { createServer } from 'node:http';
import { test } from 'node:test';

const has = (value, key) => Object.prototype.hasOwnProperty.call(value, key);
const good = { jsonrpc: '2.0', id: 1, result: {
  resultType: 'complete', content: [{ type: 'text', text: 'ok' }], isError: false,
} };
const rpcError = { jsonrpc: '2.0', id: 1, error: {
  code: -32602, message: 'synthetic invalid params',
} };
const toolError = { jsonrpc: '2.0', id: 1, result: {
  resultType: 'complete', content: [{ type: 'text', text: 'failed' }], isError: true,
} };

export function classifyToolCall({ status, body, expectedId = 1 }) {
  if (status < 200 || status >= 300) {
    return { layer: 'transport', outcome: 'HTTP_ERROR', status };
  }
  let response;
  try { response = JSON.parse(body); }
  catch { return { layer: 'protocol', outcome: 'MALFORMED_JSON' }; }
  if (!response || Array.isArray(response) || typeof response !== 'object' ||
      response.jsonrpc !== '2.0' || response.id !== expectedId ||
      has(response, 'result') === has(response, 'error')) {
    return { layer: 'protocol', outcome: 'INVALID_ENVELOPE' };
  }
  if (has(response, 'error')) {
    if (!response.error || !Number.isInteger(response.error.code) ||
        typeof response.error.message !== 'string') {
      return { layer: 'protocol', outcome: 'INVALID_ENVELOPE' };
    }
    return { layer: 'protocol', outcome: 'JSONRPC_ERROR', code: response.error.code };
  }
  const result = response.result;
  if (!result || Array.isArray(result) || typeof result !== 'object') {
    return { layer: 'protocol', outcome: 'INVALID_TOOL_RESULT' };
  }
  // Normative 2026-07-28 fallback: absent resultType means "complete".
  const resultType = has(result, 'resultType') ? result.resultType : 'complete';
  if (resultType === 'input_required') {
    return { layer: 'interaction', outcome: 'INPUT_REQUIRED' };
  }
  if (resultType !== 'complete' || !Array.isArray(result.content) ||
      (has(result, 'isError') && typeof result.isError !== 'boolean')) {
    return { layer: 'protocol', outcome: 'INVALID_TOOL_RESULT' };
  }
  return result.isError === true
    ? { layer: 'application', outcome: 'TOOL_ERROR' }
    : { layer: 'application', outcome: 'TOOL_SUCCESS' };
}

async function withPeer(t, reply) {
  const calls = [];
  const server = createServer(async (req, res) => {
    let raw = '';
    for await (const part of req) raw += part.toString('utf8');
    calls.push({ method: req.method, path: req.url, body: raw });
    const next = reply(calls.length);
    res.writeHead(next.status, { 'content-type': 'application/json' });
    res.end(typeof next.body === 'string' ? next.body : JSON.stringify(next.body));
  });
  server.listen(0, '127.0.0.1');
  await once(server, 'listening');
  t.after(() => new Promise((resolve, reject) =>
    server.close(error => error ? reject(error) : resolve())));
  return { url: `http://127.0.0.1:${server.address().port}/mcp`, calls };
}
async function onePost(url) {
  const response = await fetch(url, { method: 'POST',
    headers: { 'content-type': 'application/json', accept: 'application/json' },
    body: JSON.stringify({ jsonrpc: '2.0', id: 1, method: 'tools/call',
      params: { name: 'synthetic', arguments: {} } }),
  });
  const body = await response.text();
  return classifyToolCall({ status: response.status, body });
}
function record(t, name, outcome, calls) {
  t.diagnostic(JSON.stringify({ synthetic: true, name, outcome, postCount: calls.length }));
}
async function testCase(t, name, wire, expected) {
  const peer = await withPeer(t, () => wire);
  const actual = await onePost(peer.url);
  assert.deepEqual(actual, expected);
  assert.equal(peer.calls.length, 1);
  record(t, name, actual, peer.calls);
}

test('baseline complete -> TOOL_SUCCESS', t => testCase(t, 'baseline',
  { status: 200, body: good }, { layer: 'application', outcome: 'TOOL_SUCCESS' }));
test('503 then 200 requires explicit second POST', async t => {
  const peer = await withPeer(t, n => n === 1
    ? { status: 503, body: { note: 'synthetic outage' } }
    : { status: 200, body: good });
  const first = await onePost(peer.url);
  assert.deepEqual(first, { layer: 'transport', outcome: 'HTTP_ERROR', status: 503 });
  assert.equal(peer.calls.length, 1, 'no automatic retry by toy client');
  const second = await onePost(peer.url); // Only this explicit call creates POST #2.
  assert.deepEqual(second, { layer: 'application', outcome: 'TOOL_SUCCESS' });
  assert.equal(peer.calls.length, 2);
  record(t, 'explicit_http_503_then_200', first, peer.calls);
});
test('HTTP 200 + JSON-RPC error -> JSONRPC_ERROR', t => testCase(t, 'jsonrpc_error',
  { status: 200, body: rpcError },
  { layer: 'protocol', outcome: 'JSONRPC_ERROR', code: -32602 }));
test('HTTP 200 + tool isError -> TOOL_ERROR', t => testCase(t, 'tool_isError',
  { status: 200, body: toolError }, { layer: 'application', outcome: 'TOOL_ERROR' }));
test('HTTP 500 with success-looking body -> HTTP_ERROR', t => testCase(t, 'transport_precedence',
  { status: 500, body: good }, { layer: 'transport', outcome: 'HTTP_ERROR', status: 500 }));
test('malformed JSON -> MALFORMED_JSON', t => testCase(t, 'malformed_json',
  { status: 200, body: '{unclosed' }, { layer: 'protocol', outcome: 'MALFORMED_JSON' }));
test('result and error together -> INVALID_ENVELOPE', t => testCase(t, 'conflicting_envelope',
  { status: 200, body: { ...good, error: rpcError.error } },
  { layer: 'protocol', outcome: 'INVALID_ENVELOPE' }));
test('wrong JSON-RPC id -> INVALID_ENVELOPE', t => testCase(t, 'wrong_response_id',
  { status: 200, body: { ...good, id: 99 } },
  { layer: 'protocol', outcome: 'INVALID_ENVELOPE' }));
test('input_required is not successful completion', t => testCase(t, 'input_required',
  { status: 200, body: { jsonrpc: '2.0', id: 1, result: {
    resultType: 'input_required', inputRequests: { approval: {
      method: 'elicitation/create', params: { mode: 'form', message: 'synthetic input' },
    } },
  } } }, { layer: 'interaction', outcome: 'INPUT_REQUIRED' }));
test('legacy result without resultType -> TOOL_SUCCESS', t => testCase(t, 'legacy_resultType_absent',
  { status: 200, body: { jsonrpc: '2.0', id: 1,
    result: { content: [{ type: 'text', text: 'legacy ok' }], isError: false } } },
  { layer: 'application', outcome: 'TOOL_SUCCESS' }));
test('invalid tool content shape -> INVALID_TOOL_RESULT', t => testCase(t, 'invalid_tool_result',
  { status: 200, body: { jsonrpc: '2.0', id: 1, result: {
    resultType: 'complete', content: 'not-an-array', isError: false,
  } } }, { layer: 'protocol', outcome: 'INVALID_TOOL_RESULT' }));
