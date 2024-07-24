import React, { useEffect } from 'react';
import axios from 'axios';
import API_BASE_URL from './config';

function AvailableDatabases({ databases, onDatabasesChange, selectedDatabases, fetchDatabases, onDatabaseDelete }) {
    
    useEffect(() => {
        fetchDatabases();
    }, []);

    const handleDatabaseChange = (e) => {
        const value = e.target.value;
        const newSelectedDatabases = selectedDatabases.includes(value)
            ? selectedDatabases.filter(db => db !== value)
            : [...selectedDatabases, value];
        onDatabasesChange(newSelectedDatabases);
    };

    const handleDelete = async (databaseName) => {
        try {
            await axios.delete(`${API_BASE_URL}/vector-databases/${databaseName}`);
            onDatabaseDelete(databaseName);
            fetchDatabases();
        } catch (error) {
            console.error('Error deleting database:', error);
        }
    };

    return (
        <div className="available-databases">
            <h2>Available Vector Databases</h2>
            {databases.map((db, index) => (
                <div key={index} className="database-entry">
                    <label>
                        <input
                            type="checkbox"
                            value={db}
                            onChange={handleDatabaseChange}
                            checked={selectedDatabases.includes(db)}
                        />
                        {db}
                    </label>
                    <button onClick={() => handleDelete(db)}>Delete</button>
                </div>
            ))}
        </div>
    );
}

export default AvailableDatabases;
