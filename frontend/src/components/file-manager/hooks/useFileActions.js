import { useState, useRef, useEffect } from 'react';
import { useConfirm } from '@/hooks/useConfirm';
import { errorReason } from '@/utils/errorMessage';

export default function useFileActions({
    fileApi,
    currentPath,
    remoteGuard,
    loadDirectory,
    refreshTree,
    previewFile,
    setPreviewFile,
    clearSelection,
    toast,
    t,
}) {
    // ─── modals ──────────────────────────────────────────
    // { kind: 'newFolder' } | { kind: 'rename', entry } | { kind: 'permissions', entry } | null
    const [dialog, setDialog] = useState(null);
    const closeDialog = () => setDialog(null);
    const { confirm } = useConfirm();
    const active = useRef(null);
    active.current = { fileApi, currentPath };
    const isCurrent = () =>
        active.current?.fileApi === fileApi && active.current?.currentPath === currentPath;
    useEffect(() => {
        setDialog(null);
    }, [fileApi, currentPath]);
    useEffect(
        () => () => {
            active.current = null;
        },
        [],
    );

    const handleCreateFolder = async (name) => {
        if (remoteGuard('create folder')) return;
        try {
            await fileApi['create folder'](`${currentPath}/${name}`);
            if (!isCurrent()) return;
            toast.success(t('app.fileManager.folderCreated', 'Folder created'));
            closeDialog();
            loadDirectory(currentPath);
            refreshTree(currentPath);
        } catch (error) {
            if (!isCurrent()) return;
            toast.error(
                t('app.fileManager.failedToCreateFolder', "Couldn't create the folder. {{message}}", {
                    message: errorReason(error),
                }),
            );
        }
    };

    const handleDelete = async (target) => {
        const items = Array.isArray(target) ? target : [target];
        if (items.length === 0) return;
        if (remoteGuard('delete')) return;
        const message =
            items.length === 1
                ? `Delete "${items[0].name}"?${items[0].is_dir ? ' All contents inside will be removed.' : ''}`
                : `Delete ${items.length} items? This cannot be undone.`;
        if (
            !(await confirm({
                title: t('app.fileManager.deleteConfirmation', 'Delete confirmation'),
                message,
                confirmText: t('common.actions.delete', 'Delete'),
                variant: 'danger',
            }))
        )
            return;
        if (!isCurrent()) return;
        const failures = [];
        for (const it of items) {
            try {
                await fileApi.del(it.path);
            } catch (error) {
                failures.push(`${it.name}: ${error.message}`);
            }
        }
        if (!isCurrent()) return;
        if (failures.length === 0)
            toast.success(
                t('app.fileManager.deletedItems', {
                    count: items.length,
                    defaultValue_one: 'Deleted 1 item',
                    defaultValue_other: 'Deleted {{count}} items',
                }),
            );
        else
            toast.error(
                t('app.fileManager.failed', "Couldn't finish for: {{value}}", { value: failures.join(', ') }),
            );
        if (previewFile && items.some((i) => i.path === previewFile.path)) setPreviewFile(null);
        clearSelection();
        loadDirectory(currentPath);
    };

    const handleRename = async (entry, name) => {
        if (remoteGuard('rename')) return;
        try {
            await fileApi.rename(entry.path, name);
            if (!isCurrent()) return;
            toast.success(t('app.fileManager.renamed', 'Renamed'));
            closeDialog();
            loadDirectory(currentPath);
        } catch (error) {
            if (!isCurrent()) return;
            toast.error(
                t('app.fileManager.failedToRename', "Couldn't rename it. {{message}}", {
                    message: errorReason(error),
                }),
            );
        }
    };

    const handleChangePermissions = async (entry, mode) => {
        if (remoteGuard('change permissions')) return;
        try {
            await fileApi['change permissions'](entry.path, mode);
            if (!isCurrent()) return;
            toast.success(t('app.fileManager.permissionsUpdated', 'Permissions updated'));
            closeDialog();
            loadDirectory(currentPath);
        } catch (error) {
            if (!isCurrent()) return;
            toast.error(
                t('app.fileManager.failed2', "Couldn't do that. {{message}}", {
                    message: errorReason(error),
                }),
            );
        }
    };

    const openRenameModal = (entry) => setDialog({ kind: 'rename', entry });
    const openPermissionsModal = (entry) => setDialog({ kind: 'permissions', entry });

    return {
        dialog,
        setDialog,
        closeDialog,
        handleCreateFolder,
        handleDelete,
        handleRename,
        handleChangePermissions,
        openRenameModal,
        openPermissionsModal,
    };
}
