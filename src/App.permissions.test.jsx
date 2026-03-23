// @vitest-environment jsdom
import { act } from 'react';
import ReactDOM from 'react-dom/client';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

const apiMock = vi.hoisted(() => ({
  getProjects: vi.fn(),
  getPoints: vi.fn(),
  savePoints: vi.fn(),
  loginRequest: vi.fn(),
  adminListProjects: vi.fn(),
  adminListLayers: vi.fn(),
  adminListUsers: vi.fn(),
  adminCreateProject: vi.fn(),
  adminUpdateProject: vi.fn(),
  adminCreateLayer: vi.fn(),
  adminUpdateLayer: vi.fn(),
  adminDeleteLayer: vi.fn(),
  adminAttachLayerToProject: vi.fn(),
  adminDetachLayerFromProject: vi.fn(),
  adminReplaceFormFields: vi.fn(),
  adminCreateUser: vi.fn(),
  adminUpdateUser: vi.fn(),
  adminAssignUserProject: vi.fn(),
  adminUnassignUserProject: vi.fn(),
  adminListGeoServerWorkspaces: vi.fn(),
  adminListGeoServerWorkspaceLayers: vi.fn(),
  adminListGeoServerWorkspaceStyles: vi.fn(),
  adminListGeoServerLayerStyles: vi.fn(),
}));

vi.mock('./lib/api', () => ({
  getProjects: apiMock.getProjects,
  getPoints: apiMock.getPoints,
  savePoints: apiMock.savePoints,
  loginRequest: apiMock.loginRequest,
  adminListProjects: apiMock.adminListProjects,
  adminListLayers: apiMock.adminListLayers,
  adminListUsers: apiMock.adminListUsers,
  adminCreateProject: apiMock.adminCreateProject,
  adminUpdateProject: apiMock.adminUpdateProject,
  adminCreateLayer: apiMock.adminCreateLayer,
  adminUpdateLayer: apiMock.adminUpdateLayer,
  adminDeleteLayer: apiMock.adminDeleteLayer,
  adminAttachLayerToProject: apiMock.adminAttachLayerToProject,
  adminDetachLayerFromProject: apiMock.adminDetachLayerFromProject,
  adminReplaceFormFields: apiMock.adminReplaceFormFields,
  adminCreateUser: apiMock.adminCreateUser,
  adminUpdateUser: apiMock.adminUpdateUser,
  adminAssignUserProject: apiMock.adminAssignUserProject,
  adminUnassignUserProject: apiMock.adminUnassignUserProject,
  adminListGeoServerWorkspaces: apiMock.adminListGeoServerWorkspaces,
  adminListGeoServerWorkspaceLayers: apiMock.adminListGeoServerWorkspaceLayers,
  adminListGeoServerWorkspaceStyles: apiMock.adminListGeoServerWorkspaceStyles,
  adminListGeoServerLayerStyles: apiMock.adminListGeoServerLayerStyles,
}));

vi.mock('./components/MapView', () => ({
  default: function MapViewMock() {
    return <div data-testid="map-view" />;
  },
}));

vi.mock('./components/RightPanel', () => ({
  default: function RightPanelMock() {
    return <div data-testid="right-panel" />;
  },
}));

vi.mock('./components/FAB', () => ({
  default: function FabMock() {
    return <div data-testid="fab" />;
  },
}));

import App from './App';

globalThis.IS_REACT_ACT_ENVIRONMENT = true;

function wait(ms = 0) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

async function waitFor(check, timeoutMs = 1200) {
  const started = Date.now();
  while (Date.now() - started < timeoutMs) {
    if (check()) return;
    await act(async () => {
      await wait(10);
    });
  }
  throw new Error('Timed out waiting for condition');
}

describe('admin permission rendering and routing', () => {
  let container;
  let root;

  beforeEach(() => {
    vi.clearAllMocks();
    localStorage.clear();
    window.history.pushState({}, '', '/');

    container = document.createElement('div');
    document.body.innerHTML = '';
    document.body.appendChild(container);
    root = ReactDOM.createRoot(container);

    apiMock.getPoints.mockResolvedValue([]);
    apiMock.savePoints.mockResolvedValue([]);
    apiMock.adminListProjects.mockResolvedValue([]);
    apiMock.adminListLayers.mockResolvedValue([]);
    apiMock.adminListUsers.mockResolvedValue([]);
    apiMock.adminListGeoServerWorkspaces.mockResolvedValue([]);
    apiMock.adminListGeoServerWorkspaceLayers.mockResolvedValue([]);
    apiMock.adminListGeoServerWorkspaceStyles.mockResolvedValue([]);
    apiMock.adminListGeoServerLayerStyles.mockResolvedValue([]);
  });

  afterEach(() => {
    act(() => {
      root.unmount();
    });
  });

  it('shows admin menu item only for admin roles and navigates to /admin', async () => {
    localStorage.setItem('token', 'test-token');
    apiMock.getProjects.mockResolvedValue([
      { id: 1, name: 'Project 1', role: 'ProjectAdmin', center: [-77.0, -12.0], zoom: 12 },
    ]);

    await act(async () => {
      root.render(<App />);
    });

    await waitFor(() => container.textContent.includes('OMI Visor'));

    const userTrigger = container.querySelector('.user-trigger');
    expect(userTrigger).toBeTruthy();

    await act(async () => {
      userTrigger.dispatchEvent(new MouseEvent('click', { bubbles: true }));
    });

    const adminButton = Array.from(container.querySelectorAll('.user-dropdown button')).find(
      (button) => button.textContent.includes('Administracion'),
    );
    expect(adminButton).toBeTruthy();

    await act(async () => {
      adminButton.dispatchEvent(new MouseEvent('click', { bubbles: true }));
      await wait(20);
    });

    await waitFor(() => container.textContent.includes('Administración'));
    expect(window.location.pathname).toBe('/admin');
  });

  it('blocks /admin route for non-admin memberships', async () => {
    localStorage.setItem('token', 'test-token');
    window.history.pushState({}, '', '/admin');
    apiMock.getProjects.mockResolvedValue([
      { id: 1, name: 'Project 1', role: 'Editor', center: [-77.0, -12.0], zoom: 12 },
    ]);

    await act(async () => {
      root.render(<App />);
    });

    await waitFor(() => container.textContent.includes('Esta cuenta no tiene permisos de administración.'));

    const backButton = Array.from(container.querySelectorAll('button')).find((button) =>
      button.textContent.includes('Volver al visor'),
    );
    expect(backButton).toBeTruthy();
  });

  it('hides admin menu item for non-admin users', async () => {
    localStorage.setItem('token', 'test-token');
    apiMock.getProjects.mockResolvedValue([
      { id: 1, name: 'Project 1', role: 'Viewer', center: [-77.0, -12.0], zoom: 12 },
    ]);

    await act(async () => {
      root.render(<App />);
    });

    await waitFor(() => container.textContent.includes('OMI Visor'));

    const userTrigger = container.querySelector('.user-trigger');
    await act(async () => {
      userTrigger.dispatchEvent(new MouseEvent('click', { bubbles: true }));
    });

    const adminButton = Array.from(container.querySelectorAll('.user-dropdown button')).find(
      (button) => button.textContent.includes('Administracion'),
    );
    expect(adminButton).toBeFalsy();
  });
});
