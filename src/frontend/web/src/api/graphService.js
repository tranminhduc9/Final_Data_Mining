import { apiClient } from '../utils/apiClient';

// GET /graph/explore — keywords: array[string], depth: integer (default 1)
export const exploreGraph = async (keywords = [], depth = 1) => {
    const params = new URLSearchParams();
    keywords.forEach(kw => params.append('keywords', kw));
    params.append('depth', depth);
    return await apiClient(`/graph/explore?${params.toString()}`, { method: 'GET' });
};

export const fetchGraphData = exploreGraph;

// GET /graph/road_analysis — from: string, to: string
export const analyzeRoad = async (from, to) => {
    const params = new URLSearchParams();
    params.append('from', from);
    params.append('to', to);
    return await apiClient(`/graph/road_analysis?${params.toString()}`, { method: 'GET' });
};
