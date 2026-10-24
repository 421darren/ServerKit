import { useEffect, useState } from 'react';
import api from '../../services/api';

// Keep discovery and resolution together: never flatten a Compose app's
// service-specific winners into a misleading single environment.
export function useEffectiveEnvironment(appId) {
    const [selection, setSelection] = useState(null);
    const [discovery, setDiscovery] = useState(null);
    const [result, setResult] = useState(null);
    const [revision, setRevision] = useState(0);
    useEffect(() => {
        let active = true;
        setDiscovery(null);
        api.getComposeServices(appId).then(data => {
            if (active) setDiscovery({ appId, revision, services: data.services || [] });
        }).catch(() => {
            if (active) setDiscovery({ appId, revision, error: true });
        });
        return () => { active = false; };
    }, [appId, revision]);
    const current = discovery?.appId === appId && discovery?.revision === revision ? discovery : null;
    const services = current?.services || [];
    const service = selection?.appId === appId && services.includes(selection.service)
        ? selection.service : services[0] || null;
    useEffect(() => {
        if (!current || current.error) return undefined;
        let active = true;
        setResult(null);
        api.getEffectiveEnvVars(appId, service).then(data => {
            if (active) setResult({ appId, service, revision, data });
        }).catch(() => {
            if (active) setResult({ appId, service, revision, error: true });
        });
        return () => { active = false; };
    }, [appId, service, revision, current]);
    const latest = current && result?.appId === appId && result?.service === service
        && result?.revision === revision ? result : null;
    return {
        services, service, data: latest?.data,
        error: Boolean(current?.error || latest?.error),
        loading: !current || (!current.error && !latest),
        selectService: value => setSelection({ appId, service: value }),
        refresh: () => setRevision(value => value + 1),
    };
}
