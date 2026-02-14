// Mock expo-router
jest.mock('expo-router', () => ({
  useRouter: () => ({
    push: jest.fn(),
    replace: jest.fn(),
    back: jest.fn(),
    canGoBack: jest.fn(() => false),
  }),
  usePathname: () => '/',
  useGlobalSearchParams: () => ({}),
  useLocalSearchParams: () => ({}),
  useSegments: () => [],
  Stack: ({ children }) => children,
  Tabs: ({ children }) => children,
  Drawer: ({ children }) => children,
  Link: ({ children }) => children,
  router: {
    push: jest.fn(),
    replace: jest.fn(),
    back: jest.fn(),
    canGoBack: jest.fn(() => false),
  },
}));
