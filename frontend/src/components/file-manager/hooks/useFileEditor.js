import { useEffect, useRef, useState } from 'react';
import { errorReason } from '@/utils/errorMessage';

export default function useFileEditor({ fileApi, toast, t, onSaved }) {
    const [previewFile, setPreview] = useState(null);
    const [fileContent, setFileContent] = useState('');
    const [editing, setEditing] = useState(false);
    const generation = useRef(0);
    const activeApi = useRef(fileApi);
    activeApi.current = fileApi;
    useEffect(
        () => () => {
            generation.current++;
        },
        [],
    );

    const setPreviewFile = (entry) => {
        generation.current++;
        setPreview(entry);
        setFileContent('');
        setEditing(false);
    };

    const openFile = async (entry) => {
        setPreviewFile(entry);
        const request = generation.current;
        if (!entry.is_editable) return;
        try {
            const data = await fileApi.read(entry.path);
            if (request === generation.current && fileApi === activeApi.current) {
                setFileContent(data.content);
            }
        } catch (error) {
            if (request === generation.current && fileApi === activeApi.current) {
                toast.error(
                    t('app.fileManager.failedToReadFile', "Couldn't read the file. {{message}}", {
                        message: errorReason(error),
                    }),
                );
            }
        }
    };

    const handleSaveFile = async () => {
        if (!previewFile) return;
        const request = generation.current;
        try {
            await fileApi.write(previewFile.path, fileContent);
            if (request !== generation.current || fileApi !== activeApi.current) return;
            toast.success(t('app.fileManager.fileSaved', 'File saved'));
            setEditing(false);
            onSaved();
        } catch (error) {
            if (request !== generation.current || fileApi !== activeApi.current) return;
            toast.error(
                t('app.fileManager.failedToSave', "Couldn't save. {{message}}", {
                    message: errorReason(error),
                }),
            );
        }
    };

    return {
        previewFile,
        setPreviewFile,
        fileContent,
        setFileContent,
        editing,
        setEditing,
        openFile,
        handleSaveFile,
    };
}
