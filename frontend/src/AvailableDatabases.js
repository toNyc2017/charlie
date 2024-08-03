import React, { useEffect } from 'react';

function AvailableDatabases({ databases, onDatabasesChange, selectedDatabases, fetchDatabases }) {
    
    useEffect(() => {
        fetchDatabases();
    }, [fetchDatabases]);

    
    
    
    const handleDatabaseChange = (e) => {
        const value = e.target.value;
        const newSelectedDatabases = selectedDatabases.includes(value)
            ? selectedDatabases.filter(db => db !== value)
            : [...selectedDatabases, value];
        onDatabasesChange(newSelectedDatabases);
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
                        checked={selectedDatabases.includes(db)}
                    />
                    {db}
                </label>
            ))}
        </div>
    );
}

export default AvailableDatabases;
