import { defineConfig } from 'vitepress'

// https://vitepress.dev/reference/site-config
export default defineConfig({
  title: "Code Slob Cleanup",
  description: "Automated toolchain to identify, refactor, and rigorously verify Python code.",
  themeConfig: {
    // https://vitepress.dev/reference/default-theme-config
    nav: [
      { text: 'Home', link: '/' },
      { text: 'Overview', link: '/README' },
      { text: 'Scripts', link: '/scripts' },
      { text: 'Exclusions', link: '/exclusions' },
      { text: 'Workflow', link: '/workflow' },
    ],

    sidebar: [
      {
        text: 'Documentation',
        items: [
          { text: 'Overview', link: '/README' },
          { text: 'Scripts Reference', link: '/scripts' },
          { text: 'Exclusions Guide', link: '/exclusions' },
          { text: 'Workflow Automation', link: '/workflow' },
        ]
      }
    ],

    socialLinks: [
      { icon: 'github', link: 'https://github.com/Jazz23/CodeSlobCleanup' }
    ],
    
    search: {
      provider: 'local'
    }
  },
  base: '/CodeSlobCleanup/' // Essential for GitHub Pages deployment under a repository
})
