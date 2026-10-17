import { useCallback, useEffect, useState } from 'react';
import api from '../../services/api';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import Modal from '@/components/Modal';
import FormField from '@/components/FormField';
import { useToast } from '../../contexts/useToast.js';
import { useConfirm } from '../../hooks/useConfirm';
import { DataTable, DataTableFooter } from '../ds';
import EmptyState from '../EmptyState';
import { Eye, EyeOff, Mail } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import { OfflineIcon, RefreshIcon } from './serverDetailShared';

const parseMailboxes = (raw = '') => {
    return raw
        .split('\n')
        .map(line => line.trim())
        .filter(line => line.startsWith('* '))
        .map(line => {
            const email = line.slice(2).split(/\s+/)[0];
            return { email };
        })
        .filter(item => item.email);
};

const parseAliases = (raw = '') => {
    return raw
        .split('\n')
        .map(line => line.trim())
        .filter(line => line.startsWith('* '))
        .map(line => {
            const parts = line.slice(2).split(/\s+/);
            return {
                alias: parts[0] || '',
                recipient: parts.slice(1).join(' '),
            };
        })
        .filter(item => item.alias);
};

const generateMailboxPassword = () => {
    const chars = 'ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz23456789!@#$%&*';
    const length = 20;
    const values = new Uint32Array(length);
    window.crypto.getRandomValues(values);

    return Array.from(values, value => chars[value % chars.length]).join('');
};

const ServerMailTab = ({ serverId, serverStatus }) => {
    const { t } = useTranslation();
    const toast = useToast();
    const { confirm: confirmMailboxDelete } = useConfirm();
    const [mailboxes, setMailboxes] = useState([]);
    const [aliases, setAliases] = useState([]);
    const [subTab, setSubTab] = useState('mailboxes');
    const [loading, setLoading] = useState(true);
    const [loadError, setLoadError] = useState(null);
    const [notInstalled, setNotInstalled] = useState(false);
    const [showCreateMailbox, setShowCreateMailbox] = useState(false);
    const [mailboxEmail, setMailboxEmail] = useState('');
    const [mailboxPassword, setMailboxPassword] = useState('');
    const [showMailboxPassword, setShowMailboxPassword] = useState(false);
    const [mailboxCreateError, setMailboxCreateError] = useState('');
    const [mailboxCreating, setMailboxCreating] = useState(false);
    const [passwordMailbox, setPasswordMailbox] = useState(null);
    const [newMailboxPassword, setNewMailboxPassword] = useState('');
    const [showNewMailboxPassword, setShowNewMailboxPassword] = useState(false);
    const [passwordUpdateError, setPasswordUpdateError] = useState('');
    const [passwordUpdating, setPasswordUpdating] = useState(false);
    const [mailboxDetails, setMailboxDetails] = useState(null);
    const [mailboxDetailsLoading, setMailboxDetailsLoading] = useState(false);
    const [mailboxDetailsError, setMailboxDetailsError] = useState('');
    const [deleteMailbox, setDeleteMailbox] = useState(null);
    const [deleteMailboxBusy, setDeleteMailboxBusy] = useState(false);
    const [showCreateAlias, setShowCreateAlias] = useState(false);
    const [aliasAddress, setAliasAddress] = useState('');
    const [aliasRecipient, setAliasRecipient] = useState('');
    const [aliasCreateError, setAliasCreateError] = useState('');
    const [aliasCreating, setAliasCreating] = useState(false);
    const [editAlias, setEditAlias] = useState(null);
    const [editAliasRecipient, setEditAliasRecipient] = useState('');
    const [aliasUpdateError, setAliasUpdateError] = useState('');
    const [aliasUpdating, setAliasUpdating] = useState(false);

    const loadMailData = useCallback(async () => {
        setLoading(true);
        setLoadError(null);
        setNotInstalled(false);
        // Clear first, so a failed load never shows the previous server's data.
        setMailboxes([]);
        setAliases([]);

        try {
            const [mailboxResult, aliasResult] = await Promise.allSettled([
                api.getServerMailboxes(serverId),
                api.getServerMailAliases(serverId),
            ]);

            if (mailboxResult.status === 'fulfilled') {
                setMailboxes(parseMailboxes(mailboxResult.value?.mailboxes_raw));
            }
            if (aliasResult.status === 'fulfilled') {
                setAliases(parseAliases(aliasResult.value?.aliases_raw));
            }
            const failed = [mailboxResult, aliasResult].find(r => r.status === 'rejected');
            if (failed && failed.reason?.code === 'MAIL_SERVER_NOT_INSTALLED') {
                setNotInstalled(true);
            } else if (failed) {
                console.error('Failed to load mail data:', failed.reason);
                setLoadError(failed.reason?.message || 'Failed to load mail data');
            }
        } finally {
            setLoading(false);
        }
    }, [serverId]);

    useEffect(() => {
        if (serverStatus === 'online') {
            loadMailData();
        } else {
            setLoading(false);
        }
    }, [loadMailData, serverStatus]);

    const closeCreateMailbox = () => {
        if (mailboxCreating) return;
        setShowCreateMailbox(false);
        setMailboxEmail('');
        setMailboxPassword('');
        setMailboxCreateError('');
    };

    const handleCreateMailbox = async event => {
        event.preventDefault();

        const email = mailboxEmail.trim();
        if (!email || !mailboxPassword) {
            setMailboxCreateError('Email and password are required.');
            return;
        }

        setMailboxCreating(true);
        setMailboxCreateError('');

        try {
            await api.createServerMailbox(serverId, email, mailboxPassword);
            toast.success(`Mailbox ${email} created`);
            setShowCreateMailbox(false);
            setMailboxEmail('');
            setMailboxPassword('');
            await loadMailData();
        } catch (err) {
            setMailboxCreateError(err.message || 'Failed to create mailbox');
        } finally {
            setMailboxCreating(false);
        }
    };

    const openPasswordModal = mailbox => {
        setPasswordMailbox(mailbox);
        setNewMailboxPassword('');
        setPasswordUpdateError('');
    };

    const closePasswordModal = () => {
        if (passwordUpdating) return;
        setPasswordMailbox(null);
        setNewMailboxPassword('');
        setPasswordUpdateError('');
    };

    const openMailboxDetails = async mailbox => {
        const email = mailbox?.email;
        if (!email) return;

        setMailboxDetails({
            email,
            quota: null,
            inbox: null,
        });
        setMailboxDetailsLoading(true);
        setMailboxDetailsError('');

        try {
            const result = await api.getServerMailboxDetails(serverId, email);
            setMailboxDetails(result);
        } catch (err) {
            setMailboxDetailsError(
                err.message || `Failed to load mailbox details for ${email}`
            );
        } finally {
            setMailboxDetailsLoading(false);
        }
    };

    const closeMailboxDetails = () => {
        if (mailboxDetailsLoading) return;
        setMailboxDetails(null);
        setMailboxDetailsError('');
    };

    const generateCreateMailboxPassword = () => {
        setMailboxPassword(generateMailboxPassword());
        setMailboxCreateError('');
    };

    const generateUpdateMailboxPassword = () => {
        setNewMailboxPassword(generateMailboxPassword());
        setPasswordUpdateError('');
    };

    const handleUpdateMailboxPassword = async event => {
        event.preventDefault();

        if (!passwordMailbox?.email || !newMailboxPassword) {
            setPasswordUpdateError('A new password is required.');
            return;
        }

        setPasswordUpdating(true);
        setPasswordUpdateError('');

        try {
            await api.updateServerMailboxPassword(
                serverId,
                passwordMailbox.email,
                newMailboxPassword
            );
            toast.success(`Password updated for ${passwordMailbox.email}`);
            setPasswordMailbox(null);
            setNewMailboxPassword('');
        } catch (err) {
            setPasswordUpdateError(err.message || 'Failed to update mailbox password');
        } finally {
            setPasswordUpdating(false);
        }
    };

    const handleDeleteMailbox = mailbox => {
        const email = mailbox?.email;
        if (!email) return;

        setDeleteMailbox({
            email,
        });
    };

    const closeDeleteMailbox = () => {
        if (deleteMailboxBusy) return;
        setDeleteMailbox(null);
    };

    const executeDeleteMailbox = async deleteMailData => {
        const email = deleteMailbox?.email;
        if (!email || deleteMailboxBusy) return;

        setDeleteMailboxBusy(true);

        try {
            await api.deleteServerMailbox(
                serverId,
                email,
                deleteMailData
            );

            toast.success(
                deleteMailData
                    ? `Mailbox ${email} and its mail data deleted`
                    : `Mailbox ${email} deleted; mail data preserved`
            );

            setDeleteMailbox(null);
            await loadMailData();
        } catch (err) {
            toast.error(err.message || `Failed to delete mailbox ${email}`);
        } finally {
            setDeleteMailboxBusy(false);
        }
    };

    const closeCreateAlias = () => {
        if (aliasCreating) return;
        setShowCreateAlias(false);
        setAliasAddress('');
        setAliasRecipient('');
        setAliasCreateError('');
    };

    const handleCreateAlias = async event => {
        event.preventDefault();

        const alias = aliasAddress.trim();
        const recipient = aliasRecipient.trim();

        if (!alias || !recipient) {
            setAliasCreateError('Alias and recipient are required.');
            return;
        }

        setAliasCreating(true);
        setAliasCreateError('');

        try {
            await api.createServerMailAlias(serverId, alias, recipient);
            toast.success(`Alias ${alias} created`);
            setShowCreateAlias(false);
            setAliasAddress('');
            setAliasRecipient('');
            await loadMailData();
        } catch (err) {
            setAliasCreateError(err.message || 'Failed to create alias');
        } finally {
            setAliasCreating(false);
        }
    };

    const openEditAlias = item => {
        setEditAlias(item);
        setEditAliasRecipient(item?.recipient || '');
        setAliasUpdateError('');
    };

    const closeEditAlias = () => {
        if (aliasUpdating) return;
        setEditAlias(null);
        setEditAliasRecipient('');
        setAliasUpdateError('');
    };

    const handleUpdateAlias = async event => {
        event.preventDefault();

        const alias = editAlias?.alias;
        const oldRecipient = editAlias?.recipient;
        const newRecipient = editAliasRecipient.trim();

        if (!alias || !oldRecipient || !newRecipient) {
            setAliasUpdateError('Recipient is required.');
            return;
        }

        setAliasUpdating(true);
        setAliasUpdateError('');

        try {
            await api.updateServerMailAlias(
                serverId,
                alias,
                oldRecipient,
                newRecipient
            );
            toast.success(`Alias ${alias} updated`);
            setEditAlias(null);
            setEditAliasRecipient('');
            await loadMailData();
        } catch (err) {
            setAliasUpdateError(err.message || 'Failed to update alias');
        } finally {
            setAliasUpdating(false);
        }
    };

    const handleDeleteAlias = async item => {
        const alias = item?.alias;
        const recipient = item?.recipient;

        if (!alias || !recipient) return;

        const confirmed = await confirmMailboxDelete({
            title: 'Delete Alias',
            message: `Delete alias ${alias} → ${recipient}?`
        });

        if (!confirmed) return;

        try {
            await api.deleteServerMailAlias(serverId, alias, recipient);
            toast.success(`Alias ${alias} deleted`);
            await loadMailData();
        } catch (err) {
            toast.error(err.message || `Failed to delete alias ${alias}`);
        }
    };

    if (serverStatus !== 'online') {
        return (
            <div className="offline-notice">
                <OfflineIcon />
                <h4>{t('app.serverMailTab.serverOffline', 'Server Offline')}</h4>
                <p>{t(
                    'app.serverMailTab.mailManagementRequiresOnline',
                    'Mail management requires the server to be online.'
                )}</p>
            </div>
        );
    }

    if (loading) {
        return (
            <EmptyState
                loading
                title={t('app.serverMailTab.loadingMailData', 'Loading mail data')}
            />
        );
    }

    const mailboxColumns = [
        {
            key: 'email',
            header: 'Mailbox',
            sortable: true,
            hideable: false,
            sortValue: mailbox => mailbox.email,
            render: mailbox => mailbox.email,
        },
        {
            key: 'actions',
            headerKey: 'common.labels.actions',
            header: 'Actions',
            sortable: false,
            hideable: false,
            cellClassName: 'actions-cell',
            render: mailbox => (
                <div className="actions-cell">
                    <Button
                        variant="ghost"
                        size="sm"
                        type="button"
                        onClick={() => openMailboxDetails(mailbox)}
                    >
                        Details
                    </Button>
                    <Button
                        variant="ghost"
                        size="sm"
                        type="button"
                        onClick={() => openPasswordModal(mailbox)}
                    >
                        Change Password
                    </Button>
                    <Button
                        variant="ghost"
                        size="sm"
                        type="button"
                        onClick={() => handleDeleteMailbox(mailbox)}
                    >
                        Delete
                    </Button>
                </div>
            ),
        },
    ];

    const aliasColumns = [
        {
            key: 'alias',
            header: 'Alias',
            sortable: true,
            hideable: false,
            sortValue: item => item.alias,
            render: item => item.alias,
        },
        {
            key: 'recipient',
            header: 'Recipient',
            sortable: true,
            sortValue: item => item.recipient,
            render: item => item.recipient,
        },
        {
            key: 'actions',
            headerKey: 'common.labels.actions',
            header: 'Actions',
            sortable: false,
            hideable: false,
            cellClassName: 'actions-cell',
            render: item => (
                <div className="actions-cell">
                    <Button
                        variant="ghost"
                        size="sm"
                        type="button"
                        onClick={() => openEditAlias(item)}
                    >
                        Edit
                    </Button>
                    <Button
                        variant="ghost"
                        size="sm"
                        type="button"
                        onClick={() => handleDeleteAlias(item)}
                    >
                        Delete
                    </Button>
                </div>
            ),
        },
    ];

    if (notInstalled && !loading) {
        return (
            <div className="docker-tab">
                <EmptyState
                    icon={Mail}
                    title={t('app.serverMailTab.notInstalledTitle', 'No mail server on this server')}
                    description={t('app.serverMailTab.notInstalledDescription',
                        'Mailboxes can be managed here once a docker-mailserver container named "mailserver" is running on this server.')}
                />
            </div>
        );
    }

    return (
        <div className="docker-tab">
            {loadError && (
                <div className="docker-tab__error">
                    <strong>
                        {t('app.serverMailTab.couldNotLoad', 'Could not load mail data:')}
                    </strong>{' '}
                    {loadError}
                    <Button size="sm" variant="outline" onClick={loadMailData}>
                        <RefreshIcon /> {t('common.actions.retry', 'Retry')}
                    </Button>
                </div>
            )}

            <div className="docker-sub-tabs">
                <Button
                    variant="unstyled"
                    type="button"
                    className={`sub-tab ${subTab === 'mailboxes' ? 'active' : ''}`}
                    onClick={() => setSubTab('mailboxes')}
                >
                    Mailboxes ({mailboxes.length})
                </Button>

                <Button
                    variant="unstyled"
                    type="button"
                    className={`sub-tab ${subTab === 'aliases' ? 'active' : ''}`}
                    onClick={() => setSubTab('aliases')}
                >
                    Aliases ({aliases.length})
                </Button>

            {subTab === 'mailboxes' && (
                    <Button
                        type="button"
                        size="sm"
                        onClick={() => setShowCreateMailbox(true)}
                    >
                        + Create Mailbox
                    </Button>
                )}

                {subTab === 'aliases' && (
                    <Button
                        type="button"
                        size="sm"
                        onClick={() => setShowCreateAlias(true)}
                    >
                        + Create Alias
                    </Button>
                )}

                <Button
                    variant="outline"
                    size="sm"
                    type="button"
                    onClick={loadMailData}
                >
                    <RefreshIcon /> {t('common.actions.refresh', 'Refresh')}
                </Button>
            </div>

            {editAlias && (
                <Modal
                    open
                    onClose={closeEditAlias}
                    title={t('app.serverMailTab.editAlias', 'Edit Alias')}
                    size="md"
                >
                    <form onSubmit={handleUpdateAlias}>
                        {aliasUpdateError && (
                            <div className="error-message">{aliasUpdateError}</div>
                        )}

                        <FormField
                            label={t('app.serverMailTab.alias', 'Alias')}
                            htmlFor="edit-alias-address"
                        >
                            <Input
                                id="edit-alias-address"
                                type="email"
                                value={editAlias.alias}
                                disabled
                            />
                        </FormField>

                        <FormField
                            label={t('app.serverMailTab.recipient', 'Recipient')}
                            htmlFor="edit-alias-recipient"
                            required
                            hint={t('app.serverMailTab.aliasUpdateHint', 'Messages sent to this alias will be delivered to the updated recipient.')}
                        >
                            <Input
                                id="edit-alias-recipient"
                                type="email"
                                value={editAliasRecipient}
                                onChange={event => setEditAliasRecipient(event.target.value)}
                                autoComplete="off"
                                required
                            />
                        </FormField>

                        <div className="modal-actions">
                            <Button
                                type="button"
                                variant="outline"
                                onClick={closeEditAlias}
                                disabled={aliasUpdating}
                            >
                                Cancel
                            </Button>
                            <Button type="submit" disabled={aliasUpdating}>
                                {aliasUpdating ? t('app.serverMailTab.updating', 'Updating...') : t('app.serverMailTab.updateAlias', 'Update Alias')}
                            </Button>
                        </div>
                    </form>
                </Modal>
            )}

            {showCreateMailbox && (
                <Modal
                    open
                    onClose={closeCreateMailbox}
                    title={t('app.serverMailTab.createMailbox', 'Create Mailbox')}
                    size="md"
                >
                    <form onSubmit={handleCreateMailbox}>
                        {mailboxCreateError && (
                            <div className="error-message">{mailboxCreateError}</div>
                        )}

                        <FormField
                            label={t('app.serverMailTab.email', 'Email')}
                            htmlFor="mailbox-email"
                            required
                        >
                            <Input
                                id="mailbox-email"
                                type="email"
                                value={mailboxEmail}
                                onChange={event => setMailboxEmail(event.target.value)}
                                placeholder="user@example.com"
                                autoComplete="off"
                                required
                            />
                        </FormField>

                        <FormField
                            label={t('app.serverMailTab.password', 'Password')}
                            htmlFor="mailbox-password"
                            required
                            hint="The password is sent to docker-mailserver and is not displayed after creation."
                        >
                            <div className="mailbox-password-field">
                            <Input
                                id="mailbox-password"
                                type={showMailboxPassword ? 'text' : 'password'}
                                value={mailboxPassword}
                                onChange={event => setMailboxPassword(event.target.value)}
                                autoComplete="new-password"
                                required
                            />
                            <Button
                                type="button"
                                variant="outline"
                                onClick={() => setShowMailboxPassword(value => !value)}
                                disabled={mailboxCreating}
                                aria-label={showMailboxPassword ? 'Hide password' : 'Show password'}
                                title={showMailboxPassword ? 'Hide password' : 'Show password'}
                            >
                                {showMailboxPassword ? <EyeOff size={16} /> : <Eye size={16} />}
                            </Button>
                            <Button
                                type="button"
                                variant="outline"
                                onClick={generateCreateMailboxPassword}
                                disabled={mailboxCreating}
                            >
                                Generate Password
                            </Button>
                        </div>
                        </FormField>

                        <div className="modal-actions">
                            <Button
                                type="button"
                                variant="outline"
                                onClick={closeCreateMailbox}
                                disabled={mailboxCreating}
                            >
                                Cancel
                            </Button>
                            <Button type="submit" disabled={mailboxCreating}>
                                {mailboxCreating ? t('app.serverMailTab.creating', 'Creating...') : t('app.serverMailTab.createMailbox', 'Create Mailbox')}
                            </Button>
                        </div>
                    </form>
                </Modal>
            )}

            {deleteMailbox && (
                <Modal
                    open
                    onClose={closeDeleteMailbox}
                    title={t('app.serverMailTab.deleteMailbox', 'Delete Mailbox')}
                    size="md"
                >
                    <div>
                        <p>
                            Delete mailbox <strong>{deleteMailbox.email}</strong>?
                        </p>

                        <p>
                            Choose what should happen to the existing mailbox data.
                        </p>

                        <div className="error-message">
                            <strong>Delete Mail Data</strong>
                            permanently removes the mailbox and its stored mail.
                            This cannot be undone.
                        </div>

                        <div className="modal-actions">
                            <Button
                                type="button"
                                variant="outline"
                                onClick={closeDeleteMailbox}
                                disabled={deleteMailboxBusy}
                            >
                                Cancel
                            </Button>

                            <Button
                                type="button"
                                variant="outline"
                                onClick={() => executeDeleteMailbox(false)}
                                disabled={deleteMailboxBusy}
                            >
                                {deleteMailboxBusy
                                    ? 'Deleting...'
                                    : t('app.serverMailTab.keepMailData', 'Keep Mail Data')}
                            </Button>

                            <Button
                                type="button"
                                variant="danger"
                                onClick={() => executeDeleteMailbox(true)}
                                disabled={deleteMailboxBusy}
                            >
                                {deleteMailboxBusy
                                    ? 'Deleting...'
                                    : t('app.serverMailTab.deleteMailData', 'Delete Mail Data')}
                            </Button>
                        </div>
                    </div>
                </Modal>
            )}

            {passwordMailbox && (
                <Modal
                    open
                    onClose={closePasswordModal}
                    title={t('app.serverMailTab.changeMailboxPassword', 'Change Mailbox Password')}
                    size="md"
                >
                    <form onSubmit={handleUpdateMailboxPassword}>
                        {passwordUpdateError && (
                            <div className="error-message">{passwordUpdateError}</div>
                        )}

                        <FormField
                            label={t('app.serverMailTab.mailbox', 'Mailbox')}
                            htmlFor="password-mailbox-email"
                        >
                            <Input
                                id="password-mailbox-email"
                                type="email"
                                value={passwordMailbox.email}
                                disabled
                            />
                        </FormField>

                        <FormField
                            label={t('app.serverMailTab.newPassword', 'New Password')}
                            htmlFor="new-mailbox-password"
                            required
                            hint="The new password is sent to docker-mailserver and is not displayed after the update."
                        >
                            <div className="mailbox-password-field">
                                <Input
                                    id="new-mailbox-password"
                                    type={showNewMailboxPassword ? 'text' : 'password'}
                                    value={newMailboxPassword}
                                    onChange={event => setNewMailboxPassword(event.target.value)}
                                    autoComplete="new-password"
                                    required
                                />
                                <Button
                                    type="button"
                                    variant="outline"
                                    onClick={() => setShowNewMailboxPassword(value => !value)}
                                    disabled={passwordUpdating}
                                    aria-label={showNewMailboxPassword ? 'Hide password' : 'Show password'}
                                    title={showNewMailboxPassword ? 'Hide password' : 'Show password'}
                                >
                                    {showNewMailboxPassword ? <EyeOff size={16} /> : <Eye size={16} />}
                                </Button>
                                <Button
                                    type="button"
                                    variant="outline"
                                    onClick={generateUpdateMailboxPassword}
                                    disabled={passwordUpdating}
                                >
                                    Generate Password
                                </Button>
                            </div>
                        </FormField>

                        <div className="modal-actions">
                            <Button
                                type="button"
                                variant="outline"
                                onClick={closePasswordModal}
                                disabled={passwordUpdating}
                            >
                                Cancel
                            </Button>
                            <Button type="submit" disabled={passwordUpdating}>
                                {passwordUpdating ? 'Updating...' : 'Update Password'}
                            </Button>
                        </div>
                    </form>
                </Modal>
            )}

            {mailboxDetails && (
                <Modal
                    open
                    onClose={closeMailboxDetails}
                    title={t('app.serverMailTab.mailboxDetails', 'Mailbox Details')}
                    size="md"
                >
                    <div className="mailbox-details">
                        <FormField
                            label={t('app.serverMailTab.mailbox', 'Mailbox')}
                            htmlFor="mailbox-details-email"
                        >
                            <Input
                                id="mailbox-details-email"
                                type="email"
                                value={mailboxDetails.email || ''}
                                disabled
                            />
                        </FormField>

                        {mailboxDetailsLoading && (
                            <div className="loading-message">
                                Loading mailbox details...
                            </div>
                        )}

                        {mailboxDetailsError && (
                            <div className="error-message">
                                {mailboxDetailsError}
                            </div>
                        )}

                        {!mailboxDetailsLoading && !mailboxDetailsError && (
                            <>
                                <FormField label={t('app.serverMailTab.quota', 'Quota')}>
                                    <div className="mailbox-details__value">
                                        <div>
                                            <strong>Storage:</strong>{' '}
                                            {mailboxDetails.quota?.storage ?? '—'}
                                        </div>
                                        <div>
                                            <strong>Messages:</strong>{' '}
                                            {mailboxDetails.quota?.messages ?? '—'}
                                        </div>
                                        <div>
                                            <strong>Limit:</strong>{' '}
                                            {mailboxDetails.quota?.limit ?? t('app.serverMailTab.unlimited', 'Unlimited')}
                                        </div>
                                        <div>
                                            <strong>Usage:</strong>{' '}
                                            {mailboxDetails.quota?.percent ?? '—'}%
                                        </div>
                                    </div>
                                </FormField>

                                <FormField label={t('app.serverMailTab.inbox', 'INBOX')}>
                                    <div className="mailbox-details__value">
                                        <div>
                                            <strong>Messages:</strong>{' '}
                                            {mailboxDetails.inbox?.messages ?? '—'}
                                        </div>
                                        <div>
                                            <strong>Recent:</strong>{' '}
                                            {mailboxDetails.inbox?.recent ?? '—'}
                                        </div>
                                        <div>
                                            <strong>Unseen:</strong>{' '}
                                            {mailboxDetails.inbox?.unseen ?? '—'}
                                        </div>
                                        <div>
                                            <strong>Virtual size:</strong>{' '}
                                            {mailboxDetails.inbox?.vsize ?? '—'} bytes
                                        </div>
                                        <div>
                                            <strong>UID Next:</strong>{' '}
                                            {mailboxDetails.inbox?.uidnext ?? '—'}
                                        </div>
                                        <div>
                                            <strong>UID Validity:</strong>{' '}
                                            {mailboxDetails.inbox?.uidvalidity ?? '—'}
                                        </div>
                                        <div>
                                            <strong>Highest Modseq:</strong>{' '}
                                            {mailboxDetails.inbox?.highestmodseq ?? '—'}
                                        </div>
                                        <div>
                                            <strong>First Saved:</strong>{' '}
                                            {mailboxDetails.inbox?.firstsaved ?? '—'}
                                        </div>
                                        <div>
                                            <strong>GUID:</strong>{' '}
                                            {mailboxDetails.inbox?.guid ?? '—'}
                                        </div>
                                    </div>
                                </FormField>

                                <div className="modal-actions">
                                    <Button
                                        type="button"
                                        variant="outline"
                                        onClick={closeMailboxDetails}
                                    >
                                        Close
                                    </Button>
                                </div>
                            </>
                        )}

                        {mailboxDetailsLoading && (
                            <div className="modal-actions">
                                <Button
                                    type="button"
                                    variant="outline"
                                    onClick={closeMailboxDetails}
                                    disabled
                                >
                                    Loading...
                                </Button>
                            </div>
                        )}

                        {mailboxDetailsError && (
                            <div className="modal-actions">
                                <Button
                                    type="button"
                                    variant="outline"
                                    onClick={closeMailboxDetails}
                                >
                                    Close
                                </Button>
                            </div>
                        )}
                    </div>
                </Modal>
            )}

            {showCreateAlias && (
                <Modal
                    open
                    onClose={closeCreateAlias}
                    title={t('app.serverMailTab.createAlias', 'Create Alias')}
                    size="md"
                >
                    <form onSubmit={handleCreateAlias}>
                        {aliasCreateError && (
                            <div className="error-message">{aliasCreateError}</div>
                        )}

                        <FormField
                            label={t('app.serverMailTab.alias', 'Alias')}
                            htmlFor="alias-address"
                            required
                        >
                            <Input
                                id="alias-address"
                                type="email"
                                value={aliasAddress}
                                onChange={event => setAliasAddress(event.target.value)}
                                placeholder="sales@example.com"
                                autoComplete="off"
                                required
                            />
                        </FormField>

                        <FormField
                            label={t('app.serverMailTab.recipient', 'Recipient')}
                            htmlFor="alias-recipient"
                            required
                            hint={t('app.serverMailTab.aliasCreateHint', 'Messages sent to the alias will be delivered to this address.')}
                        >
                            <Input
                                id="alias-recipient"
                                type="email"
                                value={aliasRecipient}
                                onChange={event => setAliasRecipient(event.target.value)}
                                placeholder="user@example.com"
                                autoComplete="off"
                                required
                            />
                        </FormField>

                        <div className="modal-actions">
                            <Button
                                type="button"
                                variant="outline"
                                onClick={closeCreateAlias}
                                disabled={aliasCreating}
                            >
                                Cancel
                            </Button>
                            <Button type="submit" disabled={aliasCreating}>
                                {aliasCreating ? t('app.serverMailTab.creating', 'Creating...') : t('app.serverMailTab.createAlias', 'Create Alias')}
                            </Button>
                        </div>
                    </form>
                </Modal>
            )}

            {subTab === 'mailboxes' && (
                mailboxes.length === 0 ? (
                    <EmptyState
                        icon={Mail}
                        title={t('app.serverMailTab.noMailboxes', 'No mailboxes')}
                        description={t('app.serverMailTab.noMailboxesDescription', 'No docker-mailserver mailboxes were found on this server.')}
                    />
                ) : (
                    <DataTable
                        columns={mailboxColumns}
                        data={mailboxes}
                        keyField="email"
                        storageKey="serverkit-table-sd-mail-mailboxes"
                        tableClassName="data-table"
                        footer={
                            <DataTableFooter
                                shown={mailboxes.length}
                                total={mailboxes.length}
                                noun="mailbox"
                            />
                        }
                    />
                )
            )}

            {subTab === 'aliases' && (
                aliases.length === 0 ? (
                    <EmptyState
                        icon={Mail}
                        title={t('app.serverMailTab.noAliases', 'No aliases')}
                        description={t('app.serverMailTab.noAliasesDescription', 'No docker-mailserver aliases are configured on this server.')}
                    />
                ) : (
                    <DataTable
                        columns={aliasColumns}
                        data={aliases}
                        keyField="alias"
                        storageKey="serverkit-table-sd-mail-aliases"
                        tableClassName="data-table"
                        footer={
                            <DataTableFooter
                                shown={aliases.length}
                                total={aliases.length}
                                noun="alias"
                            />
                        }
                    />
                )
            )}
        </div>
    );
};

export default ServerMailTab;
