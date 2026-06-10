import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom';
import { Layout } from './components/Layout';
import { AuthProvider } from './context/AuthContext';
import { ContactPage } from './pages/ContactPage';
import { DiagnosticGuidesPage } from './pages/DiagnosticGuidesPage';
import { DocumentsPage } from './pages/DocumentsPage';
import { InterestLinksPage } from './pages/InterestLinksPage';
import { ManageNewsPage } from './pages/ManageNewsPage';
import { ManageUsersPage } from './pages/ManageUsersPage';
import { NewsPage } from './pages/NewsPage';
import { TreatmentProtocolsPage } from './pages/TreatmentProtocolsPage';

function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          <Route element={<Layout />}>
            <Route index element={<NewsPage />} />
            <Route path="contacto" element={<ContactPage />} />
            <Route path="enlaces" element={<InterestLinksPage />} />
            <Route path="documentos" element={<DocumentsPage />} />
            <Route path="guias-diagnostico" element={<DiagnosticGuidesPage />} />
            <Route path="protocolos-tratamiento" element={<TreatmentProtocolsPage />} />
            <Route path="gestion/noticias" element={<ManageNewsPage />} />
            <Route path="gestion/usuarios" element={<ManageUsersPage />} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
}

export default App;
