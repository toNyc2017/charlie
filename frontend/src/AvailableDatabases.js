import React, { useEffect, useState } from 'react';
import axios from 'axios';
import API_BASE_URL from './config';

function AvailableDatabases({ onDatabasesChange }) {
    const [databases, setDatabases] = useState([]);
    const [selectedDatabases, setSelectedDatabases] = useState([]);

    useEffect(() => {
        const fetchDatabases = async () => {
            const response = await axios.get(`${API_BASE_URL}/vector-databases`);
            console.log("Fetched databases:", response.data);
            setDatabases(response.data);
        };
        fetchDatabases();
    }, []);

    const handleDatabaseChange = (e) => {
        const value = e.target.value;
        const newSelectedDatabases = selectedDatabases.includes(value)
            ? selectedDatabases.filter(db => db !== value)
            : [...selectedDatabases, value];
        setSelectedDatabases(newSelectedDatabases);
        onDatabasesChange(newSelectedDatabases);
        console.log("Database has changed.  In AvailableDatabases.handleDatabaseChange:");
    };

    return (
        <div className="available-databases">
            <h2>Available Vector Databases</h2>
            {databases.map((db, index) => (
                <label key={index}>
                    <input
                        type="checkbox"
                        value={db}
                        onChange={handleDatabaseChange}
                        checked={selectedDatabases.includes(db)} // Initially unchecked
                    />
                    {db}
                </label>
            ))}
        </div>
    );
}

export default AvailableDatabases;
