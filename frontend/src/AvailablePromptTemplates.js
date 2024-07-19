import React, { useEffect, useState } from 'react';
import axios from 'axios';
import API_BASE_URL from './config';

function AvailablePromptTemplates({ onTemplateChange, templates, selectedTemplate }) {
    const [localSelectedTemplate, setLocalSelectedTemplate] = useState(selectedTemplate);

    useEffect(() => {
        const fetchTemplates = async () => {
            const response = await axios.get(`${API_BASE_URL}/prompt-templates`);
            setLocalSelectedTemplate(response.data);
        };
        fetchTemplates();
    }, []);

    const handleTemplateChange = (e) => {
        const value = e.target.value;
        setLocalSelectedTemplate(value);
        onTemplateChange(value);
    };

    return (
        <div className="available-templates">
            <h2>Available Prompt Templates</h2>
            {templates.map((template, index) => (
                <label key={index}>
                    <input
                        type="checkbox"
                        value={template}
                        onChange={handleTemplateChange}
                        checked={localSelectedTemplate === template}
                    />
                    {template}
                </label>
            ))}
        </div>
    );
}

export default AvailablePromptTemplates;
