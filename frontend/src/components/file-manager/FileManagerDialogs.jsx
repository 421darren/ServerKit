import { NamePromptModal, PermissionsModal } from './FileDialogs';

import { useTranslation } from 'react-i18next';

export default function FileManagerDialogs({
    dialog,
    currentPath,
    handleCreateFolder,
    closeDialog,
    handleRename,
    handleChangePermissions,
}) {
    const { t } = useTranslation();
    return (
        <>
            {dialog?.kind === 'newFolder' && (
                <NamePromptModal
                    title={t('app.fileManager.createNewFolder', 'Create new folder')}
                    label={t('app.fileManager.folderName', 'Folder name')}
                    placeholder="new-folder"
                    hint={
                        <p className="text-muted">
                            {t('app.fileManager.willBeCreatedIn', 'Will be created in:')}{' '}
                            <code>{currentPath}</code>
                        </p>
                    }
                    submitLabel={t('app.fileManager.createFolder', 'Create folder')}
                    onSubmit={handleCreateFolder}
                    onClose={closeDialog}
                />
            )}
            {dialog?.kind === 'rename' && (
                <NamePromptModal
                    key={dialog.entry.path}
                    title={t('app.fileManager.rename2', 'Rename {{value}}', {
                        value: dialog.entry.is_dir ? 'Folder' : 'File',
                    })}
                    label={t('app.fileManager.newName', 'New name')}
                    initialValue={dialog.entry.name}
                    submitLabel={t('app.fileManager.rename', 'Rename')}
                    onSubmit={(name) => handleRename(dialog.entry, name)}
                    onClose={closeDialog}
                />
            )}
            {dialog?.kind === 'permissions' && (
                <PermissionsModal
                    key={dialog.entry.path}
                    entry={dialog.entry}
                    onSubmit={(mode) => handleChangePermissions(dialog.entry, mode)}
                    onClose={closeDialog}
                />
            )}
        </>
    );
}
