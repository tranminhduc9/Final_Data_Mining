const http = require('http');

http.get('http://localhost:8080/api/v1/clustering/clusters/0', (res) => {
    let data = '';
    res.on('data', chunk => data += chunk);
    res.on('end', () => {
        console.log("RESPONSE from 8080 for cluster 0:");
        console.log(data);
    });
}).on('error', err => console.log('Try 8080 failed:', err.message));
