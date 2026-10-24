import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { Input } from '../ui/input';
import FormField from '../FormField';
import { Button } from '../ui/button';

export default function PreviewCreateForm({ onCreate, busy }) {
    const { t } = useTranslation();
    const [number, setNumber] = useState('');
    const [branch, setBranch] = useState('');
    const [sha, setSha] = useState('');
    async function submit(event) {
        event.preventDefault();
        await onCreate({ pr_number: Number(number), branch: branch.trim(), commit_sha: sha.trim() });
    }
    return <form onSubmit={submit} className="preview-settings">
        <p className="preview-settings__hint">{t('app.previewList.pinnedHelp', 'Deploy a branch from this application’s configured repository at an exact commit. Signed PR webhooks can also create and remove previews automatically.')}</p>
        <div className="form-row">
            <FormField htmlFor="preview-pr-number" label={t('app.previewList.prNumber', 'PR number')}>
                <Input id="preview-pr-number" type="number" min="1" step="1" required value={number} onChange={e => setNumber(e.target.value)} />
            </FormField>
            <FormField htmlFor="preview-branch" label={t('app.previewList.branch', 'Repository branch')}>
                <Input id="preview-branch" required value={branch} onChange={e => setBranch(e.target.value)} />
            </FormField>
            <FormField htmlFor="preview-commit" label={t('app.previewList.commit', 'Full commit SHA')}>
                <Input id="preview-commit" required pattern="[0-9a-fA-F]{40}|[0-9a-fA-F]{64}" value={sha} onChange={e => setSha(e.target.value)} />
            </FormField>
        </div>
        <Button type="submit" disabled={busy}>{t('app.previewList.createPreview', 'Deploy preview')}</Button>
    </form>;
}
