// Mock API cho Development (sẽ thay thế bằng /api/v1/radar sau này)
const MOCK_TRENDS = [
    { id: 1, name: 'Python', growth: 65, category: 'AI/ML', jobs: 2100 },
    { id: 2, name: 'Golang', growth: 38, category: 'Backend', jobs: 1200 },
    { id: 3, name: 'React', growth: 20, category: 'Frontend', jobs: 3500 },
    { id: 4, name: 'Node.js', growth: 15, category: 'Backend', jobs: 2800 },
];

export const fetchTrends = async (timeframe = 'monthly') => {
    return new Promise((resolve) => {
        setTimeout(() => {
            resolve({
                status: 'success',
                data: MOCK_TRENDS,
                metadata: { timeframe }
            });
        }, 600);
    });
};

/* =========================================================================
   THỰC TẾ API /api/v1/radar (Tạm thời được comment vì chưa dùng đến)
========================================================================= */
/*
// Layer 1: Lấy danh sách 4 công nghệ tăng trưởng nhanh nhất
export const getRadarTop4 = async () => {
    // Endpoint: GET /api/v1/radar/top4
    // Description: Lấy danh sách 4 công nghệ có tăng trưởng nhanh nhất trong 3 tháng gần nhất + các chỉ số
    // Response Model:
    // [
    //   { "technology": "React", "Sentiment": 1, "job_count": 1500, "YoY": 66, "growth_rate": 171 },
    //   { "technology": "Node.js", "Sentiment": 1, "job_count": 1200, "YoY": 50, "growth_rate": 120 },
    //   { "technology": "Python", "Sentiment": 1, "job_count": 2000, "YoY": 40, "growth_rate": 100 },
    //   { "technology": "Docker", "Sentiment": 1, "job_count": 800, "YoY": 30, "growth_rate": 80 }
    // ]
    const response = await fetch('/api/v1/radar/top4');
    return response.json();
};

// Layer 2: Truy vấn dữ liệu cho biểu đồ xu hướng theo form search
export const getRadarSearch = async (payload) => {
    // Endpoint: GET /api/v1/radar/search
    // Request Model: { technology: ["React", "Node.js", "Python"], time_range: 6, plot_type: "line" }
    // Response Model:
    // {
    //   "data": {
    //       "React": { "months": ["2023-01", "2023-02", ...], "job_counts": [1000, 1100, ...] },
    //       "Node.js": { "months": ["2023-01", "2023-02", ...], "job_counts": [800, 900, ...] },
    //       "Python": { "months": ["2023-01", "2023-02", ...], "job_counts": [1500, 1600, ...] }
    //   }
    // }
    const params = new URLSearchParams();
    if(payload.technology) params.append('technology', payload.technology.join(','));
    if(payload.time_range) params.append('time_range', payload.time_range);
    if(payload.plot_type) params.append('plot_type', payload.plot_type);

    const response = await fetch(`/api/v1/radar/search?${params.toString()}`);
    return response.json();
};

// Layer 2: Xuất biểu đồ xu hướng thành file PNG
export const exportRadarPng = () => {
    // Endpoint: GET /api/v1/radar/export-png
    window.location.href = '/api/v1/radar/export-png';
};

// Layer 2: Xuất dữ liệu biểu đồ xu hướng thành file CSV
export const exportRadarCsv = () => {
    // Endpoint: GET /api/v1/radar/export-csv
    window.location.href = '/api/v1/radar/export-csv';
};

// Layer 3: Lấy danh sách top 10 công nghệ
export const getRadarTop10 = async () => {
    // Endpoint: GET /api/v1/radar/top10
    // Description: Lấy danh sách top 10 công nghệ kèm số lượng jobs
    // Response Model:
    // {
    //   "data": [
    //      {"technology": "React", "job_count": 1500},
    //      {"technology": "Node.js", "job_count": 1200},
    //      {"technology": "Python", "job_count": 2000},
    //      {"technology": "Docker", "job_count": 800},
    //      {"technology": "AWS", "job_count": 900},
    //      {"technology": "Kubernetes", "job_count": 700},
    //      {"technology": "Java", "job_count": 1800},
    //      {"technology": "C#", "job_count": 1600},
    //      {"technology": "Go", "job_count": 600},
    //      {"technology": "Ruby", "job_count": 500}
    //   ]
    // }
    const response = await fetch('/api/v1/radar/top10');
    return response.json();
};
*/
