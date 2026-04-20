import { createContext, useContext, useState, useEffect } from 'react';

const AppContext = createContext();

export function AppProvider({ children }) {
    const [settings, setSettings] = useState(() => {
        const saved = localStorage.getItem('appSettings');
        if (saved) return JSON.parse(saved);
        
        // Mặc định cho phép Website hoạt động
        return { 
            isWebMaintenance: false, 
            isAppMaintenance: false,
            isChatEnabled: true, 
            isGraphEnabled: true 
        };
    });

    // Lưu state xuống Local Storage ngay khi có sự thay đổi
    useEffect(() => {
        localStorage.setItem('appSettings', JSON.stringify(settings));
    }, [settings]);

    const updateSettings = (updates) => {
        setSettings(prev => ({ ...prev, ...updates }));
    };

    return (
        <AppContext.Provider value={{ settings, updateSettings }}>
            {children}
        </AppContext.Provider>
    );
}

export const useAppContext = () => useContext(AppContext);
