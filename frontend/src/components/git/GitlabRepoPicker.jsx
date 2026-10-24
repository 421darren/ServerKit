import RepoPicker from './RepoPicker';
import { gitlabProvider } from './repoProviders';

// Thin binding of the shared RepoPicker to this provider.
const GitlabRepoPicker = ({ onPick }) => (
    <RepoPicker provider={gitlabProvider} onPick={onPick} />
);

export default GitlabRepoPicker;
