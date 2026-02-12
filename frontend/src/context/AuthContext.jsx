import React, { createContext, useContext, useState, useEffect } from 'react';

const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
    const [user, setUser] = useState(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        // Mock persistence check
        const savedUser = localStorage.getItem('aurora_user');
        if (savedUser) {
            setUser(JSON.parse(savedUser));
        }
        setLoading(false);
    }, []);

    const [operators, setOperators] = useState(() => {
        const savedOperators = localStorage.getItem('aurora_operators');
        return savedOperators ? JSON.parse(savedOperators) : [
            { id: 'OP-4921', name: 'John Doe', status: 'Active', shifts: 'Morning', securityKey: '1234' },
            { id: 'OP-5502', name: 'Sarah Miller', status: 'Active', shifts: 'Evening', securityKey: '5678' }
        ];
    });

    useEffect(() => {
        localStorage.setItem('aurora_operators', JSON.stringify(operators));
    }, [operators]);

    const addOperator = (operator) => {
        setOperators(prev => [...prev, { ...operator, status: 'Active' }]);
    };

    const deleteOperator = (id) => {
        setOperators(prev => prev.filter(op => op.id !== id));
    };

    const verifyOperator = (id, password) => {
        return operators.find(op => op.id === id && op.securityKey === password);
    };

    const login = (role, customData = null) => {
        const userData = {
            role,
            id: customData?.id || (role === 'admin' ? 'ADM-001' : 'OP-4921'),
            name: customData?.name || (role === 'admin' ? 'System Administrator' : 'Operator')
        };
        setUser(userData);
        localStorage.setItem('aurora_user', JSON.stringify(userData));
    };

    const updateProfile = (newData) => {
        const updatedUser = { ...user, ...newData };
        setUser(updatedUser);
        localStorage.setItem('aurora_user', JSON.stringify(updatedUser));
    };

    const logout = () => {
        setUser(null);
        localStorage.removeItem('aurora_user');
    };

    return (
        <AuthContext.Provider value={{
            user,
            login,
            logout,
            updateProfile,
            loading,
            operators,
            addOperator,
            deleteOperator,
            verifyOperator
        }}>
            {!loading && children}
        </AuthContext.Provider>
    );
};

export const useAuth = () => {
    const context = useContext(AuthContext);
    if (!context) {
        throw new Error('useAuth must be used within an AuthProvider');
    }
    return context;
};
