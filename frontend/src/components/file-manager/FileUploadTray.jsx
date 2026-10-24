import { X, CloudUpload } from 'lucide-react';

import { Button } from '@/components/ui/button';

import { useTranslation } from 'react-i18next';

export default function FileUploadTray({ uploads, activeUploads, totalUploadProgress, setUploads }) {
    const { t } = useTranslation();
    return (
        <>
            {uploads.length > 0 && (
                <div className="upload-tray">
                    <div className="upload-tray-header">
                        <CloudUpload size={16} />
                        <span>
                            {activeUploads.length > 0
                                ? t('app.fileManager.uploadingFiles', {
                                      count: activeUploads.length,
                                      defaultValue_one: 'Uploading 1 file…',
                                      defaultValue_other: 'Uploading {{count}} files…',
                                  })
                                : t('app.fileManager.uploadsComplete', 'Uploads complete')}
                        </span>
                        {activeUploads.length > 0 && (
                            <span className="upload-tray-percent">{Math.round(totalUploadProgress)}%</span>
                        )}
                        <Button
                            variant="unstyled"
                            type="button"
                            className="toolbar-icon-btn small"
                            onClick={() => setUploads([])}
                            title={t('common.actions.clear', 'Clear')}
                        >
                            <X size={14} />
                        </Button>
                    </div>
                    <div className="upload-tray-list">
                        {uploads.map((u) => (
                            <div key={u.id} className={`upload-tray-item status-${u.status}`}>
                                <span className="upload-name">{u.name}</span>
                                <div className="upload-bar">
                                    <div className="upload-bar-fill" style={{ width: `${u.progress}%` }} />
                                </div>
                                <span className="upload-status">
                                    {u.status === 'done'
                                        ? t('common.actions.done', 'Done')
                                        : u.status === 'error'
                                          ? t('app.fileManager.uploadFailed', 'Failed')
                                          : `${Math.round(u.progress)}%`}
                                </span>
                            </div>
                        ))}
                    </div>
                </div>
            )}
        </>
    );
}
