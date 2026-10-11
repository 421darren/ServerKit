import RepoPicker from './RepoPicker';
import { giteaProvider } from './repoProviders';

// Thin binding of the shared RepoPicker to this provider.
const GiteaRepoPicker = ({ onPick }) => (
    <RepoPicker provider={giteaProvider} onPick={onPick} />
);

export default GiteaRepoPicker;
