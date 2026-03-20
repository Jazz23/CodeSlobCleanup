<script setup>
import { onMounted } from 'vue'

onMounted(() => {
  // Try to preserve the hash for deep links
  const hash = window.location.hash || '#getting-started';
  window.location.replace("https://github.com/Jazz23/CodeSlobCleanup/blob/main/docs/README.md" + hash);
})
</script>

# Redirecting...

If you are not redirected automatically, please [click here](https://github.com/Jazz23/CodeSlobCleanup/blob/main/docs/README.md#getting-started).
