import { Folder, File } from 'lucide-react';

import { formatBytes } from './fileTypes';

import { useTranslation } from 'react-i18next';

export default function FileManagerStatus({ stats }) {
    const { t } = useTranslation();
    return (
        <>
            <div className="status-bar">
                <div className="status-bar-left">
                    <span className="status-item">
                        <span className="status-label">{t('app.fileManager.total', 'Total')}</span>
                        <span className="status-value">
                            {stats.total} item{stats.total !== 1 ? 's' : ''}
                        </span>
                    </span>
                    <span className="status-divider" />
                    <span className="status-item">
                        <Folder size={12} />
                        <span>
                            {stats.folders} folder{stats.folders !== 1 ? 's' : ''}
                        </span>
                    </span>
                    <span className="status-item">
                        <File size={12} />
                        <span>
                            {stats.files} file{stats.files !== 1 ? 's' : ''}
                        </span>
                    </span>
                    {stats.totalBytes > 0 && (
                        <>
                            <span className="status-divider" />
                            <span className="status-item">
                                <span className="status-label">{t('common.labels.size', 'Size')}</span>
                                <span className="status-value">{formatBytes(stats.totalBytes)}</span>
                            </span>
                        </>
                    )}
                </div>
                <div className="status-bar-right">
                    {stats.selectedCount > 0 && (
                        <span className="status-selection">
                            {stats.selectedCount} {t('app.fileManager.selected', 'selected ·')}{' '}
                            {formatBytes(stats.selectedBytes)}
                        </span>
                    )}
                    <span
                        className="status-shortcuts"
                        title={t('app.fileManager.keyboardShortcuts', 'Keyboard shortcuts')}
                    >
                        {t('app.fileManager.upDelDeleteF2RenameA', '⌫ Up · Del Delete · F2 Rename · ⌘A All')}
                    </span>
                </div>
            </div>
        </>
    );
}
