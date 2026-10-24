import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import EnvironmentVariables from '../EnvironmentVariables';
import SegControl from '../ds/SegControl';
import ListToolbar from '../ds/ListToolbar';
import EffectiveEnvironment from './EffectiveEnvironment';

export default function EnvironmentPanel({ appId }) {
    const { t } = useTranslation();
    const [view, setView] = useState('local');
    return <>
        <ListToolbar filters={<SegControl value={view} onChange={setView} options={[
            { value: 'local', label: t('effectiveEnv.local', 'Local variables') },
            { value: 'effective', label: t('effectiveEnv.title', 'Effective environment') },
        ]} />} />
        {view === 'local' ? <EnvironmentVariables key={appId} appId={appId} />
            : <EffectiveEnvironment key={appId} appId={appId} />}
    </>;
}
