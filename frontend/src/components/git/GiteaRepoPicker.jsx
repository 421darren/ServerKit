import RepoPicker from './RepoPicker';
import { giteaProvider } from './repoProviders';

// Thin binding over the shared picker contract. The four
// provider pickers were near-identical copies; the shape they shared now
// lives in RepoPicker and the differences in repoProviders.
const GiteaRepoPicker = ({ onPick }) => (
    <RepoPicker provider={giteaProvider} onPick={onPick} />
);

export default GiteaRepoPicker;
