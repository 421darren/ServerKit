import RepoPicker from './RepoPicker';
import { githubProvider } from './repoProviders';

// Thin binding over the shared picker contract. The four
// provider pickers were near-identical copies; the shape they shared now
// lives in RepoPicker and the differences in repoProviders.
const GithubRepoPicker = ({ onPick }) => (
    <RepoPicker provider={githubProvider} onPick={onPick} />
);

export default GithubRepoPicker;
