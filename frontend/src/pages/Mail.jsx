import { useEffect, useState } from 'react';
import api from '../services/api';
import { Button } from '@/components/ui/button';
import ServerMailTab from '../components/serverdetail/ServerMailTab';
import { Mail as MailIcon, Server as ServerIcon } from 'lucide-react';
import { useTranslation } from 'react-i18next';

const LOCAL_MAIL_TARGET = {
    id: 'local',
    name: 'Local (this server)',
    status: 'online',
    is_local: true,
};

const Mail = () => {
    const { t } = useTranslation();
    const [selectedServer, setSelectedServer] = useState(LOCAL_MAIL_TARGET);
    const [availableServers, setAvailableServers] = useState([LOCAL_MAIL_TARGET]);

    useEffect(() => {
        let cancelled = false;

        async function loadAvailableServers() {
            try {
                const data = await api.getAvailableServers();
                const servers = Array.isArray(data) && data.length > 0
                    ? data
                    : [LOCAL_MAIL_TARGET];

                if (cancelled) return;

                setAvailableServers(servers);
                setSelectedServer(prev => (
                    servers.some(server => server.id === prev.id)
                        ? prev
                        : (servers[0] || LOCAL_MAIL_TARGET)
                ));
            } catch {
                if (cancelled) return;
                setAvailableServers([LOCAL_MAIL_TARGET]);
                setSelectedServer(LOCAL_MAIL_TARGET);
            }
        }

        loadAvailableServers();

        return () => {
            cancelled = true;
        };
    }, []);

    const hasMultipleTargets = availableServers.length > 1;
    const selectedStatus = selectedServer.id === 'local'
        ? 'online'
        : selectedServer.status;

    return (
        <div className="page-container page-container--full-bleed docker-page-new dx-page">
            <div className="dx-workspace">
                <aside className="dx-docker-sidebar">
                    {hasMultipleTargets && (
                        <section className="dx-sidebar-section">
                            <div className="dx-sidebar-section-header">
                                <ServerIcon size={14} />
                                <span>{t('app.docker.targets', 'Targets')}</span>
                            </div>

                            <div className="dx-resource-nav">
                                {availableServers.map(server => (
                                    <Button
                                        variant="unstyled"
                                        type="button"
                                        key={server.id}
                                        className={`dx-resource-nav-item ${
                                            selectedServer.id === server.id ? 'active' : ''
                                        }`}
                                        onClick={() => setSelectedServer(server)}
                                    >
                                        <ServerIcon size={15} />
                                        <span>
                                            {server.name || server.hostname || server.id}
                                        </span>
                                        <strong>{server.status || 'online'}</strong>
                                    </Button>
                                ))}
                            </div>
                        </section>
                    )}

                    <section className="dx-sidebar-section">
                        <div className="dx-sidebar-section-header">
                            <MailIcon size={14} />
                            <span>Mail Server</span>
                        </div>

                        <div className="dx-inventory-list">
                            <div className="dx-inventory-item">
                                <span>Target</span>
                                <strong>
                                    {selectedServer.id === 'local' ? 'Local' : 'Remote'}
                                </strong>
                            </div>
                            <div className="dx-inventory-item">
                                <span>Status</span>
                                <strong>{selectedStatus || 'unknown'}</strong>
                            </div>
                        </div>
                    </section>
                </aside>

                <main className="dx-main">
                    <div className="dx-workbar">
                        <div className="dx-workbar-title">
                            <span>Mail</span>
                            <strong>docker-mailserver</strong>
                            {hasMultipleTargets && (
                                <em>{selectedServer.name || selectedServer.id}</em>
                            )}
                        </div>
                    </div>

                    <div className="dx-panel">
                        <ServerMailTab
                            serverId={selectedServer.id}
                            serverStatus={selectedStatus}
                        />
                    </div>
                </main>
            </div>
        </div>
    );
};

export default Mail;
