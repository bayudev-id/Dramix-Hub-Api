const fetchFromKissKH = require('./fetchFromKissKH');

// Save original fetch
const originalFetch = global.fetch;

afterEach(() => {
  global.fetch = originalFetch;
  jest.restoreAllMocks();
});

describe('fetchFromKissKH', () => {
  it('should build correct URL with path and query params', async () => {
    global.fetch = jest.fn().mockResolvedValue({
      ok: true,
      json: () => Promise.resolve({ data: 'test' })
    });

    await fetchFromKissKH('/api/DramaList/Show', { ispc: '1' });

    const calledUrl = global.fetch.mock.calls[0][0];
    expect(calledUrl).toContain('https://kisskh.do/api/DramaList/Show');
    expect(calledUrl).toContain('ispc=1');
  });

  it('should skip null and undefined query params', async () => {
    global.fetch = jest.fn().mockResolvedValue({
      ok: true,
      json: () => Promise.resolve({})
    });

    await fetchFromKissKH('/api/Test', { a: '1', b: null, c: undefined });

    const calledUrl = global.fetch.mock.calls[0][0];
    expect(calledUrl).toContain('a=1');
    expect(calledUrl).not.toContain('b=');
    expect(calledUrl).not.toContain('c=');
  });

  it('should return parsed JSON on success', async () => {
    const mockData = { title: 'Drama', episodes: 16 };
    global.fetch = jest.fn().mockResolvedValue({
      ok: true,
      json: () => Promise.resolve(mockData)
    });

    const result = await fetchFromKissKH('/api/DramaList/Show');
    expect(result).toEqual(mockData);
  });

  it('should throw timeout error on AbortError', async () => {
    global.fetch = jest.fn().mockImplementation(() => {
      const err = new Error('The operation was aborted');
      err.name = 'AbortError';
      return Promise.reject(err);
    });

    await expect(fetchFromKissKH('/api/Test')).rejects.toMatchObject({
      message: 'Upstream timeout',
      type: 'timeout'
    });
  });

  it('should throw network error on fetch failure', async () => {
    global.fetch = jest.fn().mockRejectedValue(new TypeError('fetch failed'));

    await expect(fetchFromKissKH('/api/Test')).rejects.toMatchObject({
      message: 'Gagal terhubung ke upstream',
      type: 'network'
    });
  });

  it('should throw upstream error on non-2xx response', async () => {
    global.fetch = jest.fn().mockResolvedValue({
      ok: false,
      status: 404,
      json: () => Promise.resolve({ message: 'Not Found' })
    });

    await expect(fetchFromKissKH('/api/Test')).rejects.toMatchObject({
      type: 'upstream',
      statusCode: 404,
      message: 'Not Found'
    });
  });

  it('should handle non-2xx with non-JSON body', async () => {
    global.fetch = jest.fn().mockResolvedValue({
      ok: false,
      status: 500,
      json: () => Promise.reject(new Error('not json'))
    });

    await expect(fetchFromKissKH('/api/Test')).rejects.toMatchObject({
      type: 'upstream',
      statusCode: 500
    });
  });

  it('should pass AbortController signal to fetch', async () => {
    global.fetch = jest.fn().mockResolvedValue({
      ok: true,
      json: () => Promise.resolve({})
    });

    await fetchFromKissKH('/api/Test');

    const options = global.fetch.mock.calls[0][1];
    expect(options.signal).toBeInstanceOf(AbortSignal);
  });

  it('should send Accept: application/json header', async () => {
    global.fetch = jest.fn().mockResolvedValue({
      ok: true,
      json: () => Promise.resolve({})
    });

    await fetchFromKissKH('/api/Test');

    const options = global.fetch.mock.calls[0][1];
    expect(options.headers).toEqual({ 'Accept': 'application/json' });
  });
});
