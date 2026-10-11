import RepoPicker from './RepoPicker';
import { bitbucketProvider } from './repoProviders';

// Thin binding of the shared RepoPicker to this provider.
const BitbucketRepoPicker = ({ onPick }) => (
    <RepoPicker provider={bitbucketProvider} onPick={onPick} />
);

export default BitbucketRepoPicker;
