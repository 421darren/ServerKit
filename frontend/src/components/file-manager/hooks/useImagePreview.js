import { useEffect, useState } from 'react';

// Blob lifetime belongs to the mounted thumbnail, not to the storage adapter.
export default function useImagePreview(fileApi, path) {
    const [image, setImage] = useState(null);
    useEffect(() => {
        let cancelled = false;
        let blobUrl;
        setImage(null);
        if (!fileApi?.supports('preview')) return undefined;
        fileApi
            .preview(path)
            .then((result) => {
                if (cancelled) return;
                const url = result.blob ? (blobUrl = URL.createObjectURL(result.blob)) : result.url;
                setImage({ fileApi, path, url });
            })
            .catch(() => {
                /* Render the supplied fallback on failure. */
            });
        return () => {
            cancelled = true;
            if (blobUrl) URL.revokeObjectURL(blobUrl);
        };
    }, [fileApi, path]);
    return image?.fileApi === fileApi && image?.path === path ? image.url : null;
}
