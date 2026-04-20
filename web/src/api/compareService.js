// Mock API cho Development
export const fetchCompareData = async (entity1, entity2) => {
    return new Promise((resolve) => {
        setTimeout(() => {
            resolve({
                status: 'success',
                data: {
                    comparison: [
                        { metric: 'Nhu cầu tuyển dụng', [entity1]: 'Cao', [entity2]: 'Trung bình' },
                        { metric: 'Tỉ lệ tăng trưởng YoY', [entity1]: '+65%', [entity2]: '+38%' }
                    ],
                    entities: [entity1, entity2]
                }
            });
        }, 700);
    });
};

/* =========================================================================
   THỰC TẾ API /api/v1/compare (Tạm thời được comment vì chưa dùng đến)
========================================================================= */
/*
export const getCompareSearch = async (technologies) => {
    // Endpoint: GET /api/v1/compare/search
    // Description: Truy vấn dữ liệu so sánh chi tiết xu hướng công nghệ theo form search đã nhập
    // Auth: No
    // Request Model: URL param ?technology=React,Node.js
    const params = new URLSearchParams();
    if(technologies) params.append('technology', technologies.join(','));

    const response = await fetch(`/api/v1/compare/search?${params.toString()}`);
    return response.json();
};
*/
