import axios, { AxiosResponse } from 'axios';
import Cookies from 'js-cookie';
import toast from 'react-hot-toast';

// Create axios instance
const api = axios.create({
  baseURL: process.env.REACT_APP_API_URL || 'http://localhost:8000',
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor to add auth token
api.interceptors.request.use(
  (config) => {
    const token = Cookies.get('access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor to handle errors
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Unauthorized - remove token and redirect to login
      Cookies.remove('access_token');
      window.location.href = '/login';
    } else if (error.response?.status >= 500) {
      toast.error('Server error. Please try again later.');
    } else if (error.response?.data?.detail) {
      toast.error(error.response.data.detail);
    }
    return Promise.reject(error);
  }
);

// API endpoints
const API_V1 = '/api/v1';

// Auth API
export const authAPI = {
  login: async (email: string, password: string) => {
    const formData = new FormData();
    formData.append('username', email);
    formData.append('password', password);
    
    const response: AxiosResponse = await api.post(`${API_V1}/auth/login/access-token`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  },

  register: async (email: string, password: string, fullName: string) => {
    const response: AxiosResponse = await api.post(`${API_V1}/auth/register`, {
      email,
      password,
      full_name: fullName,
    });
    return response.data;
  },

  getCurrentUser: async () => {
    const response: AxiosResponse = await api.get(`${API_V1}/users/me`);
    return response.data;
  },

  updateProfile: async (data: any) => {
    const response: AxiosResponse = await api.put(`${API_V1}/users/me`, data);
    return response.data;
  },
};

// Users API
export const usersAPI = {
  getUsers: async (params?: any) => {
    const response: AxiosResponse = await api.get(`${API_V1}/users/with-stats`, { params });
    return response.data;
  },

  getUser: async (userId: number) => {
    const response: AxiosResponse = await api.get(`${API_V1}/users/${userId}`);
    return response.data;
  },

  createUser: async (userData: any) => {
    const response: AxiosResponse = await api.post(`${API_V1}/users/`, userData);
    return response.data;
  },

  updateUser: async (userId: number, userData: any) => {
    const response: AxiosResponse = await api.put(`${API_V1}/users/${userId}`, userData);
    return response.data;
  },

  deleteUser: async (userId: number) => {
    const response: AxiosResponse = await api.delete(`${API_V1}/users/${userId}`);
    return response.data;
  },

  activateUser: async (userId: number) => {
    const response: AxiosResponse = await api.post(`${API_V1}/users/${userId}/activate`);
    return response.data;
  },

  deactivateUser: async (userId: number) => {
    const response: AxiosResponse = await api.post(`${API_V1}/users/${userId}/deactivate`);
    return response.data;
  },
};

// Plans API
export const plansAPI = {
  getPlans: async () => {
    const response: AxiosResponse = await api.get(`${API_V1}/plans/`);
    return response.data;
  },

  getAllPlans: async () => {
    const response: AxiosResponse = await api.get(`${API_V1}/plans/all`);
    return response.data;
  },

  getPlansWithStats: async () => {
    const response: AxiosResponse = await api.get(`${API_V1}/plans/with-stats`);
    return response.data;
  },

  getPlan: async (planId: number) => {
    const response: AxiosResponse = await api.get(`${API_V1}/plans/${planId}`);
    return response.data;
  },

  createPlan: async (planData: any) => {
    const response: AxiosResponse = await api.post(`${API_V1}/plans/`, planData);
    return response.data;
  },

  updatePlan: async (planId: number, planData: any) => {
    const response: AxiosResponse = await api.put(`${API_V1}/plans/${planId}`, planData);
    return response.data;
  },

  deletePlan: async (planId: number) => {
    const response: AxiosResponse = await api.delete(`${API_V1}/plans/${planId}`);
    return response.data;
  },

  activatePlan: async (planId: number) => {
    const response: AxiosResponse = await api.post(`${API_V1}/plans/${planId}/activate`);
    return response.data;
  },

  deactivatePlan: async (planId: number) => {
    const response: AxiosResponse = await api.post(`${API_V1}/plans/${planId}/deactivate`);
    return response.data;
  },
};

// Subscriptions API
export const subscriptionsAPI = {
  getSubscriptions: async (params?: any) => {
    const response: AxiosResponse = await api.get(`${API_V1}/subscriptions/`, { params });
    return response.data;
  },

  getMySubscriptions: async () => {
    const response: AxiosResponse = await api.get(`${API_V1}/subscriptions/me`);
    return response.data;
  },

  getActiveSubscription: async () => {
    const response: AxiosResponse = await api.get(`${API_V1}/subscriptions/me/active`);
    return response.data;
  },

  createSubscription: async (subscriptionData: any) => {
    const response: AxiosResponse = await api.post(`${API_V1}/subscriptions/`, subscriptionData);
    return response.data;
  },

  cancelSubscription: async (subscriptionId: number) => {
    const response: AxiosResponse = await api.post(`${API_V1}/subscriptions/${subscriptionId}/cancel`);
    return response.data;
  },

  renewSubscription: async (subscriptionId: number, paymentAmount: number, paymentId?: string) => {
    const response: AxiosResponse = await api.post(`${API_V1}/subscriptions/${subscriptionId}/renew`, {
      payment_amount: paymentAmount,
      payment_id: paymentId,
    });
    return response.data;
  },

  getAnalytics: async () => {
    const response: AxiosResponse = await api.get(`${API_V1}/subscriptions/analytics`);
    return response.data;
  },
};

// Usage API
export const usageAPI = {
  getUsage: async (params?: any) => {
    const response: AxiosResponse = await api.get(`${API_V1}/usage/`, { params });
    return response.data;
  },

  getMyUsage: async (params?: any) => {
    const response: AxiosResponse = await api.get(`${API_V1}/usage/me`, { params });
    return response.data;
  },

  getMonthlyUsage: async (year: number, month: number) => {
    const response: AxiosResponse = await api.get(`${API_V1}/usage/me/monthly/${year}/${month}`);
    return response.data;
  },

  getAnalytics: async (params?: any) => {
    const response: AxiosResponse = await api.get(`${API_V1}/usage/analytics`, { params });
    return response.data;
  },

  getActiveCall: async () => {
    const response: AxiosResponse = await api.get(`${API_V1}/usage/active-calls`);
    return response.data;
  },
};

// Dashboard API
export const dashboardAPI = {
  getUserDashboard: async () => {
    const response: AxiosResponse = await api.get(`${API_V1}/dashboard/user`);
    return response.data;
  },

  getAdminDashboard: async () => {
    const response: AxiosResponse = await api.get(`${API_V1}/dashboard/admin`);
    return response.data;
  },

  getOverviewStats: async () => {
    const response: AxiosResponse = await api.get(`${API_V1}/dashboard/stats/overview`);
    return response.data;
  },

  getGrowthStats: async () => {
    const response: AxiosResponse = await api.get(`${API_V1}/dashboard/stats/growth`);
    return response.data;
  },
};

// Billing API
export const billingAPI = {
  getMyInvoices: async () => {
    const response: AxiosResponse = await api.get(`${API_V1}/billing/invoices/me`);
    return response.data;
  },

  getAllInvoices: async (params?: any) => {
    const response: AxiosResponse = await api.get(`${API_V1}/billing/invoices`, { params });
    return response.data;
  },

  getRevenueSummary: async (params?: any) => {
    const response: AxiosResponse = await api.get(`${API_V1}/billing/revenue/summary`, { params });
    return response.data;
  },

  processPayment: async (planId: number, paymentMethod: string, paymentToken?: string) => {
    const response: AxiosResponse = await api.post(`${API_V1}/billing/process-payment`, {
      plan_id: planId,
      payment_method: paymentMethod,
      payment_token: paymentToken,
    });
    return response.data;
  },

  processRefund: async (subscriptionId: number, refundAmount?: number, reason?: string) => {
    const response: AxiosResponse = await api.post(`${API_V1}/billing/refund/${subscriptionId}`, {
      refund_amount: refundAmount,
      reason,
    });
    return response.data;
  },
};

export default api;
