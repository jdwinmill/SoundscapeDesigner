import { usePage } from '@inertiajs/react';
import DesignerPage from '../../Components/Designer/DesignerPage';

export default function Edit() {
    const { soundscape } = usePage().props;
    return <DesignerPage soundscape={soundscape} />;
}
