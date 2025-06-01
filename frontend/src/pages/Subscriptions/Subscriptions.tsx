import React, { useState } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  TextField,
  InputAdornment,
  Chip,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Alert,
  CircularProgress,
  useTheme,
  Avatar,
  Grid,
} from '@mui/material';
import {
  Search as SearchIcon,
  Add as AddIcon,
  Payment as PaymentIcon,
  Person as PersonIcon,
  Business as BusinessIcon,
  Warning as WarningIcon,
  CheckCircle as CheckCircleIcon,
} from '@mui/icons-material';
import { DataGrid, GridColDef, GridActionsCellItem } from '@mui/x-data-grid';
import { useQuery, useMutation, useQueryClient } from 'react-query';
import { subscriptionsAPI, plansAPI } from '../../services/api';
import { useAuth } from '../../contexts/AuthContext';
import toast from 'react-hot-toast';

interface Subscription {
  id: number;
  user_id: number;
  plan_id: number;
  start_date: string;
  end_date: string;
  is_active: boolean;
  payment_status: string;
  payment_amount: number;
  payment_method: string;
  created_at: string;
  user?: {
    id: number;
    email: string;
    full_name: string;
  };
  plan?: {
    id: number;
    name: string;
    price: number;
  };
}

const Subscriptions: React.FC = () => {
  const theme = useTheme();
  const queryClient = useQueryClient();
  const { user } = useAuth();
  const isAdmin = user?.is_superuser;
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [paymentStatusFilter, setPaymentStatusFilter] = useState('');
  const [renewDialogOpen, setRenewDialogOpen] = useState(false);
  const [selectedSubscription, setSelectedSubscription] = useState<Subscription | null>(null);

  const { data: subscriptions, isLoading, error } = useQuery(
    ['subscriptions', searchTerm, statusFilter, paymentStatusFilter],
    () => {
      if (!isAdmin) {
        return subscriptionsAPI.getMySubscriptions();
      }
      
      const params: any = {};
      if (searchTerm) params.user_email = searchTerm;
      if (statusFilter !== '') params.is_active = statusFilter === 'true';
      if (paymentStatusFilter) params.payment_status = paymentStatusFilter;
      
      return subscriptionsAPI.getSubscriptions(params);
    },
    {
      keepPreviousData: true,
    }
  );

  const { data: plans } = useQuery('plans', plansAPI.getPlans);

  const renewSubscriptionMutation = useMutation(
    ({ id, paymentAmount }: { id: number; paymentAmount: number }) =>
      subscriptionsAPI.renewSubscription(id, paymentAmount),
    {
      onSuccess: () => {
        queryClient.invalidateQueries(['subscriptions']);
        toast.success('Subscription renewed successfully');
        setRenewDialogOpen(false);
        setSelectedSubscription(null);
      },
      onError: (error: any) => {
        toast.error(error.response?.data?.detail || 'Failed to renew subscription');
      },
    }
  );

  const cancelSubscriptionMutation = useMutation(subscriptionsAPI.cancelSubscription, {
    onSuccess: () => {
      queryClient.invalidateQueries(['subscriptions']);
      toast.success('Subscription cancelled successfully');
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to cancel subscription');
    },
  });

  const handleRenewSubscription = (subscription: Subscription) => {
    setSelectedSubscription(subscription);
    setRenewDialogOpen(true);
  };

  const handleConfirmRenewal = () => {
    if (selectedSubscription) {
      renewSubscriptionMutation.mutate({
        id: selectedSubscription.id,
        paymentAmount: selectedSubscription.plan?.price || selectedSubscription.payment_amount,
      });
    }
  };

  const handleCancelSubscription = (subscriptionId: number) => {
    if (window.confirm('Are you sure you want to cancel this subscription?')) {
      cancelSubscriptionMutation.mutate(subscriptionId);
    }
  };

  const getStatusColor = (isActive: boolean, endDate: string) => {
    if (!isActive) return 'error';
    const now = new Date();
    const end = new Date(endDate);
    const daysUntilExpiry = Math.ceil((end.getTime() - now.getTime()) / (1000 * 60 * 60 * 24));
    
    if (daysUntilExpiry <= 7) return 'warning';
    return 'success';
  };

  const getStatusLabel = (isActive: boolean, endDate: string) => {
    if (!isActive) return 'Cancelled';
    const now = new Date();
    const end = new Date(endDate);
    const daysUntilExpiry = Math.ceil((end.getTime() - now.getTime()) / (1000 * 60 * 60 * 24));
    
    if (daysUntilExpiry <= 0) return 'Expired';
    if (daysUntilExpiry <= 7) return 'Expiring Soon';
    return 'Active';
  };

  const getPaymentStatusColor = (status: string) => {
    switch (status.toLowerCase()) {
      case 'completed':
        return 'success';
      case 'pending':
        return 'warning';
      case 'failed':
        return 'error';
      default:
        return 'default';
    }
  };

  const columns: GridColDef[] = [
    ...(isAdmin ? [{
      field: 'user',
      headerName: 'User',
      flex: 1,
      minWidth: 200,
      renderCell: (params: any) => (
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <Avatar sx={{ width: 32, height: 32 }}>
            <PersonIcon />
          </Avatar>
          <Box>
            <Typography variant="body2" fontWeight="bold">
              {params.value?.full_name || 'Unknown'}
            </Typography>
            <Typography variant="caption" color="text.secondary">
              {params.value?.email}
            </Typography>
          </Box>
        </Box>
      ),
    }] : []),
    {
      field: 'plan',
      headerName: 'Plan',
      flex: 1,
      minWidth: 150,
      renderCell: (params) => (
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <Avatar sx={{ width: 32, height: 32, bgcolor: theme.palette.primary.main }}>
            <BusinessIcon />
          </Avatar>
          <Box>
            <Typography variant="body2" fontWeight="bold">
              {params.value?.name || 'Unknown Plan'}
            </Typography>
            <Typography variant="caption" color="text.secondary">
              ${params.value?.price || 0}
            </Typography>
          </Box>
        </Box>
      ),
    },
    {
      field: 'status',
      headerName: 'Status',
      width: 130,
      renderCell: (params) => (
        <Chip
          label={getStatusLabel(params.row.is_active, params.row.end_date)}
          color={getStatusColor(params.row.is_active, params.row.end_date) as any}
          size="small"
        />
      ),
    },
    {
      field: 'payment_status',
      headerName: 'Payment',
      width: 120,
      renderCell: (params) => (
        <Chip
          label={params.value}
          color={getPaymentStatusColor(params.value) as any}
          size="small"
          variant="outlined"
        />
      ),
    },
    {
      field: 'end_date',
      headerName: 'Expires',
      width: 120,
      renderCell: (params) => new Date(params.value).toLocaleDateString(),
    },
    {
      field: 'payment_amount',
      headerName: 'Amount',
      width: 100,
      renderCell: (params) => `$${params.value}`,
    },
    {
      field: 'actions',
      type: 'actions',
      headerName: 'Actions',
      width: 120,
      getActions: (params) => {
        const actions = [];
        
        if (params.row.is_active) {
          actions.push(
            <GridActionsCellItem
              icon={<PaymentIcon />}
              label="Renew"
              onClick={() => handleRenewSubscription(params.row)}
            />
          );
        }
        
        if (isAdmin || params.row.is_active) {
          actions.push(
            <GridActionsCellItem
              icon={<WarningIcon />}
              label="Cancel"
              onClick={() => handleCancelSubscription(params.row.id)}
            />
          );
        }
        
        return actions;
      },
    },
  ];

  if (error) {
    return (
      <Alert severity="error" sx={{ mb: 3 }}>
        Failed to load subscriptions. Please try again.
      </Alert>
    );
  }

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 4 }}>
        <Typography variant="h4" fontWeight="bold">
          {isAdmin ? 'Subscriptions Management' : 'My Subscriptions'}
        </Typography>
        {!isAdmin && (
          <Button
            variant="contained"
            startIcon={<AddIcon />}
            onClick={() => window.open('/plans', '_blank')}
          >
            Subscribe to Plan
          </Button>
        )}
      </Box>

      {/* Summary Cards for Admin */}
      {isAdmin && subscriptions && (
        <Grid container spacing={3} sx={{ mb: 4 }}>
          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center' }}>
                  <Avatar sx={{ bgcolor: theme.palette.primary.main, mr: 2 }}>
                    <CheckCircleIcon />
                  </Avatar>
                  <Box>
                    <Typography color="text.secondary" variant="body2">
                      Active Subscriptions
                    </Typography>
                    <Typography variant="h4" fontWeight="bold">
                      {subscriptions.filter((s: Subscription) => s.is_active).length}
                    </Typography>
                  </Box>
                </Box>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center' }}>
                  <Avatar sx={{ bgcolor: theme.palette.warning.main, mr: 2 }}>
                    <WarningIcon />
                  </Avatar>
                  <Box>
                    <Typography color="text.secondary" variant="body2">
                      Expiring Soon
                    </Typography>
                    <Typography variant="h4" fontWeight="bold">
                      {subscriptions.filter((s: Subscription) => {
                        const daysUntilExpiry = Math.ceil(
                          (new Date(s.end_date).getTime() - new Date().getTime()) / (1000 * 60 * 60 * 24)
                        );
                        return s.is_active && daysUntilExpiry <= 7 && daysUntilExpiry > 0;
                      }).length}
                    </Typography>
                  </Box>
                </Box>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center' }}>
                  <Avatar sx={{ bgcolor: theme.palette.success.main, mr: 2 }}>
                    <PaymentIcon />
                  </Avatar>
                  <Box>
                    <Typography color="text.secondary" variant="body2">
                      Monthly Revenue
                    </Typography>
                    <Typography variant="h4" fontWeight="bold">
                      ${subscriptions
                        .filter((s: Subscription) => s.is_active && s.payment_status === 'completed')
                        .reduce((sum: number, s: Subscription) => sum + s.payment_amount, 0)
                        .toFixed(0)}
                    </Typography>
                  </Box>
                </Box>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center' }}>
                  <Avatar sx={{ bgcolor: theme.palette.error.main, mr: 2 }}>
                    <WarningIcon />
                  </Avatar>
                  <Box>
                    <Typography color="text.secondary" variant="body2">
                      Failed Payments
                    </Typography>
                    <Typography variant="h4" fontWeight="bold">
                      {subscriptions.filter((s: Subscription) => s.payment_status === 'failed').length}
                    </Typography>
                  </Box>
                </Box>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      )}

      {/* Filters */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Grid container spacing={2}>
            {isAdmin && (
              <Grid item xs={12} sm={6} md={4}>
                <TextField
                  fullWidth
                  placeholder="Search by user email..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  InputProps={{
                    startAdornment: (
                      <InputAdornment position="start">
                        <SearchIcon />
                      </InputAdornment>
                    ),
                  }}
                />
              </Grid>
            )}
            <Grid item xs={12} sm={6} md={4}>
              <FormControl fullWidth>
                <InputLabel>Status</InputLabel>
                <Select
                  value={statusFilter}
                  onChange={(e) => setStatusFilter(e.target.value)}
                  label="Status"
                >
                  <MenuItem value="">All</MenuItem>
                  <MenuItem value="true">Active</MenuItem>
                  <MenuItem value="false">Cancelled</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12} sm={6} md={4}>
              <FormControl fullWidth>
                <InputLabel>Payment Status</InputLabel>
                <Select
                  value={paymentStatusFilter}
                  onChange={(e) => setPaymentStatusFilter(e.target.value)}
                  label="Payment Status"
                >
                  <MenuItem value="">All</MenuItem>
                  <MenuItem value="completed">Completed</MenuItem>
                  <MenuItem value="pending">Pending</MenuItem>
                  <MenuItem value="failed">Failed</MenuItem>
                </Select>
              </FormControl>
            </Grid>
          </Grid>
        </CardContent>
      </Card>

      {/* Subscriptions Table */}
      <Card>
        <Box sx={{ height: 600, width: '100%' }}>
          <DataGrid
            rows={subscriptions || []}
            columns={columns}
            loading={isLoading}
            pageSizeOptions={[10, 25, 50]}
            initialState={{
              pagination: {
                paginationModel: { pageSize: 25 },
              },
            }}
            disableRowSelectionOnClick
          />
        </Box>
      </Card>

      {/* Renewal Dialog */}
      <Dialog open={renewDialogOpen} onClose={() => setRenewDialogOpen(false)}>
        <DialogTitle>Renew Subscription</DialogTitle>
        <DialogContent>
          <Typography sx={{ mb: 2 }}>
            Are you sure you want to renew this subscription?
          </Typography>
          {selectedSubscription && (
            <Box>
              <Typography variant="body2" color="text.secondary">
                Plan: {selectedSubscription.plan?.name}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Amount: ${selectedSubscription.plan?.price || selectedSubscription.payment_amount}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Current expiry: {new Date(selectedSubscription.end_date).toLocaleDateString()}
              </Typography>
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setRenewDialogOpen(false)}>Cancel</Button>
          <Button
            onClick={handleConfirmRenewal}
            variant="contained"
            disabled={renewSubscriptionMutation.isLoading}
          >
            {renewSubscriptionMutation.isLoading ? <CircularProgress size={20} /> : 'Renew'}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default Subscriptions;
