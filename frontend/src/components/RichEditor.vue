<template>
  <div class="editor-wrap">
    <div class="toolbar" v-if="editor" role="toolbar" aria-label="Панель форматирования">
      <div class="toolbar-group">
        <button :class="{ active: editor.isActive('bold') }" type="button" title="Жирный" @click="run('toggleBold')">
          <strong>B</strong>
        </button>
        <button :class="{ active: editor.isActive('italic') }" type="button" title="Курсив" @click="run('toggleItalic')">
          <em>I</em>
        </button>
      </div>
      <span class="toolbar-sep"></span>
      <div class="toolbar-group">
        <button :class="{ active: editor.isActive('heading', { level: 2 }) }" type="button" title="H2" @click="runHeading(2)">H2</button>
        <button :class="{ active: editor.isActive('heading', { level: 3 }) }" type="button" title="H3" @click="runHeading(3)">H3</button>
      </div>
      <span class="toolbar-sep"></span>
      <div class="toolbar-group">
        <button :class="{ active: editor.isActive('bulletList') }" type="button" title="Маркированный список" @click="run('toggleBulletList')">
          <AppIcon name="list" :size="16" />
        </button>
        <button :class="{ active: editor.isActive('orderedList') }" type="button" title="Нумерованный список" @click="run('toggleOrderedList')">
          <AppIcon name="list-ordered" :size="16" />
        </button>
      </div>
      <span class="toolbar-sep"></span>
      <div class="toolbar-group">
        <button :class="{ active: editor.isActive('codeBlock') }" type="button" title="Блок кода" @click="runCodeBlock">
          <AppIcon name="code" :size="16" />
        </button>
      </div>
      <div class="toolbar-right">
        <button type="button" title="Отменить" @click="run('undo')">
          <AppIcon name="undo" :size="16" />
        </button>
        <button type="button" title="Повторить" @click="run('redo')">
          <AppIcon name="redo" :size="16" />
        </button>
      </div>
    </div>
    <EditorContent v-if="editor" class="editor" :editor="editor" />
  </div>
</template>

<script setup>
import { Editor } from "@tiptap/core";
import { EditorContent } from "@tiptap/vue-3";
import StarterKit from "@tiptap/starter-kit";
import CodeBlockLowlight from "@tiptap/extension-code-block-lowlight";
import Collaboration from "@tiptap/extension-collaboration";
import CollaborationCursor from "@tiptap/extension-collaboration-cursor";
import { common, createLowlight } from "lowlight";
import { onBeforeUnmount, shallowRef, watch } from "vue";
import AppIcon from "./icons/AppIcon.vue";

const props = defineProps({
  modelValue: { type: String, default: "" },
  ydoc: { type: Object, default: null },
  awareness: { type: Object, default: null },
  currentUser: { type: Object, default: null }
});

const emit = defineEmits(["update:modelValue"]);
const lowlight = createLowlight(common);
const editor = shallowRef(null);

function buildExtensions() {
  const collab = Boolean(props.ydoc);
  const extensions = [
    StarterKit.configure({ codeBlock: false, history: !collab }),
    CodeBlockLowlight.configure({ lowlight })
  ];
  if (props.ydoc) {
    extensions.push(
      Collaboration.configure({
        document: props.ydoc
      })
    );
  }
  if (props.awareness && props.currentUser?.name) {
    extensions.push(
      CollaborationCursor.configure({
        provider: { awareness: props.awareness },
        user: {
          name: props.currentUser.name,
          color: props.currentUser.color || "#3b82f6"
        }
      })
    );
  }
  return extensions;
}

function destroyEditor() {
  if (editor.value) {
    editor.value.destroy();
    editor.value = null;
  }
}

function createEditor() {
  destroyEditor();
  if (props.ydoc && !props.currentUser?.name) {
    return;
  }
  editor.value = new Editor({
    content: props.modelValue || "",
    editorProps: { attributes: { class: "tiptap-content" } },
    extensions: buildExtensions(),
    onUpdate({ editor: current }) {
      emit("update:modelValue", current.getHTML());
    }
  });
}

watch(
  () => [props.currentUser?.id, props.currentUser?.name, props.ydoc, props.awareness],
  () => {
    createEditor();
  },
  { immediate: true, flush: "post" }
);

watch(
  () => props.modelValue,
  (value) => {
    if (props.ydoc || !editor.value) {
      return;
    }
    const current = editor.value.getHTML();
    if (value !== current) {
      editor.value.commands.setContent(value || "", false);
    }
  }
);

function getHTML() {
  return editor.value ? editor.value.getHTML() : "";
}

function run(cmd) {
  editor.value?.chain().focus()[cmd]().run();
}

function runHeading(level) {
  editor.value?.chain().focus().toggleHeading({ level }).run();
}

function runCodeBlock() {
  editor.value?.chain().focus().toggleCodeBlock().run();
}

onBeforeUnmount(() => {
  destroyEditor();
});

defineExpose({ getHTML });
</script>

<style scoped>
.editor-wrap {
  border: 1.5px solid var(--border);
  border-radius: var(--radius-md);
  overflow: hidden;
  background: var(--surface);
}

.toolbar {
  display: flex;
  align-items: center;
  gap: 2px;
  padding: 6px 10px;
  border-bottom: 1px solid var(--border);
  background: var(--surface-muted);
  flex-wrap: wrap;
}

.toolbar-group {
  display: flex;
  gap: 2px;
}

.toolbar-sep {
  width: 1px;
  height: 20px;
  background: var(--border);
  margin: 0 4px;
}

.toolbar-right {
  margin-left: auto;
  display: flex;
  gap: 2px;
}

.toolbar button {
  min-width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  border: 1px solid transparent;
  border-radius: var(--radius-xs);
  background: transparent;
  color: var(--text-secondary);
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: all var(--transition-fast);
}

.toolbar button:hover {
  background: var(--surface);
  border-color: var(--border);
  color: var(--text-primary);
}

.toolbar button.active {
  background: var(--brand-500);
  border-color: var(--brand-500);
  color: white;
}

.editor {
  min-height: 400px;
  background: white;
}

:deep(.tiptap-content) {
  min-height: 400px;
  padding: 16px 20px;
  outline: none;
  line-height: 1.7;
  font-size: 15px;
}

:deep(.tiptap-content h2) {
  margin-top: 1.5em;
}

:deep(.tiptap-content h3) {
  margin-top: 1.2em;
}

:deep(.tiptap-content pre) {
  background: #0f172a;
  color: #e2e8f0;
  border-radius: var(--radius-sm);
  padding: 16px;
  overflow-x: auto;
  font-size: 13px;
  line-height: 1.6;
}

:deep(.tiptap-content code) {
  font-family: "Cascadia Code", "JetBrains Mono", "Fira Code", Consolas, monospace;
}

:deep(.tiptap-content > *:first-child) {
  margin-top: 0;
}

:deep(.collaboration-cursor__caret) {
  border-left: 2px solid;
  margin-left: -1px;
  pointer-events: none;
  position: relative;
}

:deep(.collaboration-cursor__label) {
  position: absolute;
  top: -1.4em;
  left: -1px;
  font-size: 11px;
  font-weight: 600;
  padding: 1px 6px;
  border-radius: 3px 3px 3px 0;
  white-space: nowrap;
  color: white;
}
</style>
