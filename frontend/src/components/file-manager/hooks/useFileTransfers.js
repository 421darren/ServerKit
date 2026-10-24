import { useState, useRef, useEffect } from 'react';
export default function useFileTransfers({ fileApi, currentPath, remoteGuard, loadDirectory, toast, t }) {
    // ─── upload ──────────────────────────────────────────
    const [uploads, setUploads] = useState([]);
    const [dragActive, setDragActive] = useState(false);
    const fileInputRef = useRef(null);
    const dragCounter = useRef(0);
    const nextBatch = useRef(0);
    const timers = useRef(new Set());
    const mounted = useRef(true);
    const active = useRef(null);
    active.current = { fileApi, currentPath };
    useEffect(() => {
        mounted.current = true;
        const pendingTimers = timers.current;
        return () => {
            mounted.current = false;
            pendingTimers.forEach(clearTimeout);
        };
    }, []);

    // ─── upload ──────────────────────────────────────────
    const uploadFiles = async (files) => {
        const fileList = Array.from(files);
        if (fileList.length === 0) return;
        if (remoteGuard('upload')) return;
        const batch = ++nextBatch.current;
        const queue = fileList.map((f, i) => ({
            id: `${batch}-${i}`,
            name: f.name,
            size: f.size,
            progress: 0,
            status: 'pending',
        }));
        setUploads((p) => [...p, ...queue]);

        let succeeded = 0;
        for (let i = 0; i < fileList.length; i++) {
            if (!mounted.current) return;
            const file = fileList[i];
            const itemId = queue[i].id;
            try {
                setUploads((p) => p.map((u) => (u.id === itemId ? { ...u, status: 'uploading' } : u)));
                const doUpload = fileApi.upload;
                await doUpload(currentPath, file, (progress) => {
                    if (!mounted.current) return;
                    setUploads((p) => p.map((u) => (u.id === itemId ? { ...u, progress } : u)));
                });
                if (!mounted.current) return;
                setUploads((p) =>
                    p.map((u) => (u.id === itemId ? { ...u, status: 'done', progress: 100 } : u)),
                );
                succeeded++;
            } catch (error) {
                if (!mounted.current) return;
                setUploads((p) =>
                    p.map((u) => (u.id === itemId ? { ...u, status: 'error', error: error.message } : u)),
                );
            }
        }
        if (succeeded > 0)
            toast.success(
                t('app.fileManager.uploadedFiles', {
                    count: fileList.length,
                    succeeded,
                    defaultValue_one: 'Uploaded {{succeeded}} of 1 file',
                    defaultValue_other: 'Uploaded {{succeeded}} of {{count}} files',
                }),
            );
        if (active.current.fileApi === fileApi && active.current.currentPath === currentPath) {
            loadDirectory(currentPath);
        }
        const ids = new Set(queue.map((item) => item.id));
        const timer = setTimeout(() => {
            timers.current.delete(timer);
            setUploads((p) => p.filter((u) => !ids.has(u.id)));
        }, 4000);
        timers.current.add(timer);
    };

    const handleUploadInput = (e) => {
        if (e.target.files) uploadFiles(e.target.files);
        if (fileInputRef.current) fileInputRef.current.value = '';
    };

    const handleDragEnter = (e) => {
        e.preventDefault();
        e.stopPropagation();
        dragCounter.current += 1;
        if (e.dataTransfer.items?.length > 0) setDragActive(true);
    };
    const handleDragLeave = (e) => {
        e.preventDefault();
        e.stopPropagation();
        dragCounter.current -= 1;
        if (dragCounter.current === 0) setDragActive(false);
    };
    const handleDragOver = (e) => {
        e.preventDefault();
        e.stopPropagation();
    };
    const handleDrop = (e) => {
        e.preventDefault();
        e.stopPropagation();
        dragCounter.current = 0;
        setDragActive(false);
        if (e.dataTransfer.files?.length > 0) uploadFiles(e.dataTransfer.files);
    };

    const activeUploads = uploads.filter((u) => u.status === 'uploading' || u.status === 'pending');
    const totalUploadProgress =
        activeUploads.length > 0
            ? activeUploads.reduce((s, u) => s + u.progress, 0) / activeUploads.length
            : 0;

    return {
        uploads,
        setUploads,
        dragActive,
        fileInputRef,
        handleUploadInput,
        handleDragEnter,
        handleDragLeave,
        handleDragOver,
        handleDrop,
        activeUploads,
        totalUploadProgress,
    };
}
