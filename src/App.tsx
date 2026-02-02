import { useState } from 'react';
import type { Agency, Program } from './types';
import { Layout } from './components/Layout';
import { AgencyList } from './components/AgencyList';
import { ProgramList } from './components/ProgramList';
import { ProgramDetail } from './components/ProgramDetail';

type ViewState =
  | { type: 'agencies' }
  | { type: 'programs'; agency: Agency }
  | { type: 'detail'; agency: Agency; program: Program };

function App() {
  const [view, setView] = useState<ViewState>({ type: 'agencies' });

  const handleSelectAgency = (agency: Agency) => {
    setView({ type: 'programs', agency });
  };

  const handleSelectProgram = (program: Program) => {
    if (view.type === 'programs') {
      setView({ type: 'detail', agency: view.agency, program });
    }
  };

  const handleBackToAgencies = () => {
    setView({ type: 'agencies' });
  };

  const handleBackToPrograms = () => {
    if (view.type === 'detail') {
      setView({ type: 'programs', agency: view.agency });
    }
  };

  const handleHomeClick = () => {
    setView({ type: 'agencies' });
  };

  return (
    <Layout onHomeClick={handleHomeClick}>
      {view.type === 'agencies' && (
        <AgencyList onSelectAgency={handleSelectAgency} />
      )}
      {view.type === 'programs' && (
        <ProgramList
          agency={view.agency}
          onSelectProgram={handleSelectProgram}
          onBack={handleBackToAgencies}
        />
      )}
      {view.type === 'detail' && (
        <ProgramDetail
          program={view.program}
          agency={view.agency}
          onBack={handleBackToPrograms}
        />
      )}
    </Layout>
  );
}

export default App;
