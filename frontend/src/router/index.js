import { createRouter, createWebHistory } from 'vue-router'
import WelcomePage from '../views/WelcomePage.vue'
import Layout from '../views/Layout.vue'
import FileManager from '../views/FileManager.vue'
import ChatPage from '../views/ChatPage.vue'

const routes = [
  { path: '/', component: WelcomePage },
  {
    path: '/app',
    component: Layout,
    children: [
      { path: '', redirect: '/app/chat' },
      { path: 'chat', component: ChatPage },
      { path: 'files', component: FileManager }
    ]
  }
]

export default createRouter({
  history: createWebHistory(),
  routes
})