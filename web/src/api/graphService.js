// Mock API cho Development
const MOCK_GRAPH = {
    nodes: [
        { id: 'Python', group: 1, label: 'Ngôn ngữ' },
        { id: 'TensorFlow', group: 2, label: 'Thư viện' }
    ],
    links: [
        { source: 'Python', target: 'TensorFlow', value: 4 }
    ]
};

export const fetchGraphData = async () => {
    return new Promise((resolve) => {
        setTimeout(() => {
            resolve({
                status: 'success',
                data: MOCK_GRAPH
            });
        }, 800);
    });
};

/* =========================================================================
   THỰC TẾ API /api/v1/graph (Tạm thời được comment vì chưa dùng đến)
========================================================================= */
/*
export const exploreGraph = async (payload) => {
    // Endpoint: GET /api/v1/graph/explore
    // Description: Truy vấn dữ liệu để khám phá đồ thị xu hướng theo form search
    // Auth: No
    // Request Model: { nodes: ["React", "Node.js"], depth: 1, filter: true, focus: false, reset: false }
    const params = new URLSearchParams();
    if(payload.nodes) params.append('nodes', payload.nodes.join(','));
    if(payload.depth) params.append('depth', payload.depth);
    if(payload.filter !== undefined) params.append('filter', payload.filter);
    if(payload.focus !== undefined) params.append('focus', payload.focus);
    if(payload.reset !== undefined) params.append('reset', payload.reset);

    const response = await fetch(`/api/v1/graph/explore?${params.toString()}`);
    return response.json();
};

export const filterGraph = async (payload) => {
    // Endpoint: GET /api/v1/graph/filter
    // Description: Truy vấn dữ liệu để lọc sâu trên đồ thị xu hướng
    // Auth: No
    // Request Model: { min_salary: 500, min_sentiment: 0.5, location: "Hà Nội" }
    const params = new URLSearchParams();
    if(payload.min_salary) params.append('min_salary', payload.min_salary);
    if(payload.min_sentiment) params.append('min_sentiment', payload.min_sentiment);
    if(payload.location) params.append('location', payload.location);

    const response = await fetch(`/api/v1/graph/filter?${params.toString()}`);
    return response.json();
};
*/
