import RepoPicker from './RepoPicker';
import { githubProvider } from './repoProviders';

// Thin binding of the shared RepoPicker to this provider.
const GithubRepoPicker = ({ onPick }) => (
    <RepoPicker provider={githubProvider} onPick={onPick} />
);

export default GithubRepoPicker;
