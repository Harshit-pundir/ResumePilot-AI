(() => {
    'use strict';
    const label = (item) => {
        if (typeof item === 'string' || typeof item === 'number') return String(item).trim();
        if (!item || typeof item !== 'object') return '';
        const value = item.canonical_skill || item.skill || item.name || item.label || item.value;
        return typeof value === 'string' || typeof value === 'number' ? String(value).trim() : '';
    };
    const items = (values) => Array.isArray(values) ? values.map(label).filter(Boolean) : [];
    if (typeof window !== 'undefined') window.ResumePilotSkillUtils = { items };
    if (typeof module !== 'undefined' && module.exports) module.exports = { items };
})();
