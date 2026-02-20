const http = require('http');

const request = http.get('http://127.0.0.1:8000/', (response) => {
  response.resume();
  if (response.statusCode >= 200 && response.statusCode < 500) {
    process.exit(0);
  }
  process.exit(1);
});

request.on('error', () => process.exit(1));
request.setTimeout(4000, () => {
  request.destroy();
  process.exit(1);
});
