import { useState } from 'react';
import { Wrench, Check, AlertTriangle, Loader2, ChevronDown } from 'lucide-react';
import { useServerkitAI } from '../../contexts/useServerkitAI.js';
import { useTranslation } from 'react-i18next';
import { Button as SharedButton } from '@/components/ui/button';
import { useOperations } from '../../contexts/OperationsContext';
import { useShellDock } from '../../contexts/useShellDock';

const deploymentOperation = (call) => {
    if (!['core__execute_deployment_proposal', 'core__get_deployment_operation'].includes(call.name)) return null;
    try {
        const result = typeof call.output === 'string' ? JSON.parse(call.output) : call.output;
        const operation = result?.operation;
        return operation?.run_kind === 'deploy' && typeof operation.id === 'string'
            && /^[a-f0-9-]{36}$/i.test(operation.id) ? operation : null;
    } catch { return null; }
};

// Strip the "<prefix>__" namespace for display (e.g. core__list_apps -> list_apps).
const displayName = (qualified) => {
    if (!qualified) return 'tool';
    const idx = qualified.indexOf('__');
    return idx === -1 ? qualified : qualified.slice(idx + 2);
};

const formatValue = (v) => {
    if (v == null) return '';
    if (typeof v === 'string') return v;
    try { return JSON.stringify(v, null, 2); } catch { return String(v); }
};

const ToolCallCard = ({ call }) => {
    const { t } = useTranslation();
    const { getToolRenderer } = useServerkitAI();
    const { openRun } = useOperations();
    const { openTab } = useShellDock();
    const [expanded, setExpanded] = useState(call.status === 'running');
    const Custom = getToolRenderer(call.name);
    const operation = deploymentOperation(call);

    const statusIcon = call.status === 'running'
        ? <Loader2 size={14} className="sk-ai-spin" />
        : call.isError
            ? <AlertTriangle size={14} />
            : <Check size={14} />;

    const inputText = Object.keys(call.input || {}).length
        ? formatValue(call.input)
        : (call.inputRaw || '');

    return (
        <div className={`sk-ai-tool-card${call.isError ? ' sk-ai-tool-card--error' : ''}`}>
            <SharedButton variant="unstyled"
                type="button"
                className="sk-ai-tool-card__head"
                onClick={() => setExpanded((v) => !v)}
                aria-expanded={expanded}
            >
                <Wrench size={14} />
                <span className="sk-ai-tool-card__name">{displayName(call.name)}</span>
                <span className={`sk-ai-tool-card__status sk-ai-tool-card__status--${call.status}`}>
                    {statusIcon}
                </span>
                <ChevronDown size={14} className={`sk-ai-tool-card__chev${expanded ? ' is-open' : ''}`} />
            </SharedButton>
            {operation && (
                <div className="sk-ai-tool-card__body">
                    <SharedButton type="button" variant="ghost" size="sm" onClick={() => {
                        openTab('ops');
                        openRun('deploy', operation.id);
                    }}>
                        {t('ai.openOperation', 'Open in Operations')}
                    </SharedButton>
                </div>
            )}
            {expanded && (
                <div className="sk-ai-tool-card__body">
                    {Custom ? (
                        <Custom input={call.input} output={call.output} isError={call.isError} />
                    ) : (
                        <>
                            {inputText ? (
                                <div className="sk-ai-tool-card__section">
                                    <div className="sk-ai-tool-card__label">{t('app.toolCallCard.arguments', 'Arguments')}</div>
                                    <pre className="sk-ai-code"><code>{inputText}</code></pre>
                                </div>
                            ) : null}
                            {call.output != null ? (
                                <div className="sk-ai-tool-card__section">
                                    <div className="sk-ai-tool-card__label">{t('app.toolCallCard.result', 'Result')}</div>
                                    <pre className="sk-ai-code sk-ai-tool-card__result"><code>{formatValue(call.output)}</code></pre>
                                </div>
                            ) : null}
                        </>
                    )}
                </div>
            )}
        </div>
    );
};

export default ToolCallCard;
