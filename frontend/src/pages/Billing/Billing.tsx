import React, { useState } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Button,
  Grid,
  Chip,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Alert,
  CircularProgress,
  useTheme,
  Avatar,
  Divider,
  List,
  ListItem,
  ListItemText,
  ListItemAvatar,
} from '@mui/material';
import {
  Payment as PaymentIcon,
  Receipt as ReceiptIcon,
  Download as DownloadIcon,
  CreditCard as CreditCardIcon,
  AccountBalance as AccountBalanceIcon,
  TrendingUp as TrendingUpIcon,
  AttachMoney as AttachMoneyIcon,
} from '@mui/icons-material';
import { DataGrid, GridColDef, GridActionsCellItem } from '@mui/x-data-grid';
import { useQuery, useMutation, useQueryClient } from 'react-query';
import { billingAPI, plansAPI } from '../../services/api';
import { useAuth } from '../../contexts/AuthContext';
import toast from 'react-hot-toast';

interface Invoice {
  id: number;
  subscription_id: number;
  amount: number;
  status: string;
  payment_method: string;
  payment_date: string;
  due_date: string;
  created_at: string;
  subscription?: {
    plan?: {
      name: string;
    };
  };
}

interface Plan {
  id: number;
  name: string;
  description: string;
  price: number;
  duration_days: number;
  max_calls: number;
  max_minutes: number;
  features: string;
  is_active: boolean;
}

const Billing: React.FC = () => {
  const theme = useTheme();
  const queryClient = useQueryClient();
  const { user } = useAuth();
  const isAdmin = user?.is_superuser;
  const [paymentDialogOpen, setPaymentDialogOpen] = useState(false);
  const [selectedPlan, setSelectedPlan] = useState<Plan | null>(null);
  const [paymentData, setPaymentData] = useState({
    paymentMethod: 'credit_card',
    cardNumber: '',
    expiryDate: '',
    cvv: '',
    billingAddress: '',
  });

  const { data: invoices, isLoading: invoicesLoading, error: invoicesError } = useQuery(
    'invoices',
    () => isAdmin ? billingAPI.getAllInvoices() : billingAPI.getMyInvoices()
  );

  const { data: plans, isLoading: plansLoading } = useQuery('plans', plansAPI.getPlans);

  const { data: revenueSummary } = useQuery(
    'revenue-summary',
    billingAPI.getRevenueSummary,
    {
      enabled: isAdmin,
    }
  );

  const processPaymentMutation = useMutation(
    ({ planId, paymentMethod }: { planId: number; paymentMethod: string }) =>
      billingAPI.processPayment(planId, paymentMethod),
    {
      onSuccess: () => {
        queryClient.invalidateQueries(['invoices']);
        queryClient.invalidateQueries(['subscriptions']);
        toast.success('Payment processed successfully!');
        setPaymentDialogOpen(false);
        setSelectedPlan(null);
      },
      onError: (error: any) => {
        toast.error(error.response?.data?.detail || 'Payment failed. Please try again.');
      },
    }
  );

  const handleSubscribeToPlan = (plan: Plan) => {
    setSelectedPlan(plan);
    setPaymentDialogOpen(true);
  };

  const handleProcessPayment = () => {
    if (selectedPlan) {
      processPaymentMutation.mutate({
        planId: selectedPlan.id,
        paymentMethod: paymentData.paymentMethod,
      });
    }
  };

  const handleDownloadInvoice = (invoiceId: number) => {
    // In a real app, this would download the invoice PDF
    toast.info('Invoice download feature coming soon!');
  };

  const getInvoiceStatusColor = (status: string) => {
    switch (status.toLowerCase()) {
      case 'paid':
        return 'success';
      case 'pending':
        return 'warning';
      case 'overdue':
        return 'error';
      default:
        return 'default';
    }
  };

  const formatFeatures = (features: string) => {
    return features.split(',').map(feature => feature.trim()).filter(Boolean);
  };

  const invoiceColumns: GridColDef[] = [
    {
      field: 'id',
      headerName: 'Invoice #',
      width: 100,
      renderCell: (params) => `#${params.value}`,
    },
    {
      field: 'subscription',
      headerName: 'Plan',
      flex: 1,
      minWidth: 150,
      renderCell: (params) => params.value?.plan?.name || 'Unknown Plan',
    },
    {
      field: 'amount',
      headerName: 'Amount',
      width: 120,
      renderCell: (params) => `$${params.value}`,
    },
    {
      field: 'status',
      headerName: 'Status',
      width: 120,
      renderCell: (params) => (
        <Chip
          label={params.value}
          color={getInvoiceStatusColor(params.value) as any}
          size="small"
        />
      ),
    },
    {
      field: 'payment_method',
      headerName: 'Method',
      width: 120,
    },
    {
      field: 'payment_date',
      headerName: 'Paid Date',
      width: 120,
      renderCell: (params) => params.value ? new Date(params.value).toLocaleDateString() : '-',
    },
    {
      field: 'due_date',
      headerName: 'Due Date',
      width: 120,
      renderCell: (params) => new Date(params.value).toLocaleDateString(),
    },
    {
      field: 'actions',
      type: 'actions',
      headerName: 'Actions',
      width: 100,
      getActions: (params) => [
        <GridActionsCellItem
          icon={<DownloadIcon />}
          label="Download"
          onClick={() => handleDownloadInvoice(params.row.id)}
        />,
      ],
    },
  ];

  if (invoicesError) {
    return (
      <Alert severity="error" sx={{ mb: 3 }}>
        Failed to load billing data. Please try again.
      </Alert>
    );
  }

  return (
    <Box>
      <Typography variant="h4" fontWeight="bold" sx={{ mb: 4 }}>
        {isAdmin ? 'Billing & Revenue' : 'Billing & Payments'}
      </Typography>

      {/* Revenue Summary for Admin */}
      {isAdmin && revenueSummary && (
        <Grid container spacing={3} sx={{ mb: 4 }}>
          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center' }}>
                  <Avatar sx={{ bgcolor: theme.palette.primary.main, mr: 2 }}>
                    <AttachMoneyIcon />
                  </Avatar>
                  <Box>
                    <Typography color="text.secondary" variant="body2">
                      Total Revenue
                    </Typography>
                    <Typography variant="h4" fontWeight="bold">
                      ${revenueSummary.total_revenue || 0}
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
                    <TrendingUpIcon />
                  </Avatar>
                  <Box>
                    <Typography color="text.secondary" variant="body2">
                      Monthly Revenue
                    </Typography>
                    <Typography variant="h4" fontWeight="bold">
                      ${revenueSummary.monthly_revenue || 0}
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
                    <ReceiptIcon />
                  </Avatar>
                  <Box>
                    <Typography color="text.secondary" variant="body2">
                      Pending Invoices
                    </Typography>
                    <Typography variant="h4" fontWeight="bold">
                      {invoices?.filter((inv: Invoice) => inv.status === 'pending').length || 0}
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
                    <PaymentIcon />
                  </Avatar>
                  <Box>
                    <Typography color="text.secondary" variant="body2">
                      Overdue Invoices
                    </Typography>
                    <Typography variant="h4" fontWeight="bold">
                      {invoices?.filter((inv: Invoice) => inv.status === 'overdue').length || 0}
                    </Typography>
                  </Box>
                </Box>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      )}

      {/* Available Plans for Users */}
      {!isAdmin && (
        <Card sx={{ mb: 4 }}>
          <CardContent>
            <Typography variant="h6" fontWeight="bold" sx={{ mb: 3 }}>
              Available Plans
            </Typography>
            {plansLoading ? (
              <CircularProgress />
            ) : (
              <Grid container spacing={3}>
                {plans?.filter((plan: Plan) => plan.is_active).map((plan: Plan) => (
                  <Grid item xs={12} md={6} lg={4} key={plan.id}>
                    <Card variant="outlined">
                      <CardContent>
                        <Typography variant="h6" fontWeight="bold" sx={{ mb: 1 }}>
                          {plan.name}
                        </Typography>
                        <Typography color="text.secondary" sx={{ mb: 2 }}>
                          {plan.description}
                        </Typography>
                        <Typography variant="h4" fontWeight="bold" color="primary" sx={{ mb: 2 }}>
                          ${plan.price}
                        </Typography>
                        <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                          per {plan.duration_days} days
                        </Typography>
                        <List dense>
                          <ListItem>
                            <ListItemText
                              primary={`${plan.max_calls === 0 ? 'Unlimited' : plan.max_calls} calls`}
                            />
                          </ListItem>
                          <ListItem>
                            <ListItemText
                              primary={`${plan.max_minutes === 0 ? 'Unlimited' : plan.max_minutes} minutes`}
                            />
                          </ListItem>
                          {formatFeatures(plan.features).slice(0, 2).map((feature, index) => (
                            <ListItem key={index}>
                              <ListItemText primary={feature} />
                            </ListItem>
                          ))}
                        </List>
                        <Button
                          fullWidth
                          variant="contained"
                          onClick={() => handleSubscribeToPlan(plan)}
                          sx={{ mt: 2 }}
                        >
                          Subscribe
                        </Button>
                      </CardContent>
                    </Card>
                  </Grid>
                ))}
              </Grid>
            )}
          </CardContent>
        </Card>
      )}

      {/* Invoices Table */}
      <Card>
        <CardContent>
          <Typography variant="h6" fontWeight="bold" sx={{ mb: 3 }}>
            {isAdmin ? 'All Invoices' : 'My Invoices'}
          </Typography>
          <Box sx={{ height: 400, width: '100%' }}>
            <DataGrid
              rows={invoices || []}
              columns={invoiceColumns}
              loading={invoicesLoading}
              pageSizeOptions={[10, 25, 50]}
              initialState={{
                pagination: {
                  paginationModel: { pageSize: 10 },
                },
              }}
              disableRowSelectionOnClick
            />
          </Box>
        </CardContent>
      </Card>

      {/* Payment Dialog */}
      <Dialog open={paymentDialogOpen} onClose={() => setPaymentDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Subscribe to {selectedPlan?.name}</DialogTitle>
        <DialogContent>
          <Box sx={{ pt: 2 }}>
            {selectedPlan && (
              <Card variant="outlined" sx={{ mb: 3 }}>
                <CardContent>
                  <Typography variant="h6" fontWeight="bold">
                    {selectedPlan.name}
                  </Typography>
                  <Typography color="text.secondary" sx={{ mb: 2 }}>
                    {selectedPlan.description}
                  </Typography>
                  <Typography variant="h4" fontWeight="bold" color="primary">
                    ${selectedPlan.price}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    per {selectedPlan.duration_days} days
                  </Typography>
                </CardContent>
              </Card>
            )}

            <FormControl fullWidth sx={{ mb: 3 }}>
              <InputLabel>Payment Method</InputLabel>
              <Select
                value={paymentData.paymentMethod}
                onChange={(e) => setPaymentData({ ...paymentData, paymentMethod: e.target.value })}
                label="Payment Method"
              >
                <MenuItem value="credit_card">Credit Card</MenuItem>
                <MenuItem value="paypal">PayPal</MenuItem>
                <MenuItem value="bank_transfer">Bank Transfer</MenuItem>
              </Select>
            </FormControl>

            {paymentData.paymentMethod === 'credit_card' && (
              <>
                <TextField
                  fullWidth
                  label="Card Number"
                  value={paymentData.cardNumber}
                  onChange={(e) => setPaymentData({ ...paymentData, cardNumber: e.target.value })}
                  placeholder="1234 5678 9012 3456"
                  sx={{ mb: 2 }}
                />
                <Grid container spacing={2} sx={{ mb: 2 }}>
                  <Grid item xs={6}>
                    <TextField
                      fullWidth
                      label="Expiry Date"
                      value={paymentData.expiryDate}
                      onChange={(e) => setPaymentData({ ...paymentData, expiryDate: e.target.value })}
                      placeholder="MM/YY"
                    />
                  </Grid>
                  <Grid item xs={6}>
                    <TextField
                      fullWidth
                      label="CVV"
                      value={paymentData.cvv}
                      onChange={(e) => setPaymentData({ ...paymentData, cvv: e.target.value })}
                      placeholder="123"
                    />
                  </Grid>
                </Grid>
                <TextField
                  fullWidth
                  label="Billing Address"
                  value={paymentData.billingAddress}
                  onChange={(e) => setPaymentData({ ...paymentData, billingAddress: e.target.value })}
                  multiline
                  rows={2}
                />
              </>
            )}

            <Alert severity="info" sx={{ mt: 2 }}>
              This is a demo. No actual payment will be processed.
            </Alert>
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setPaymentDialogOpen(false)}>Cancel</Button>
          <Button
            onClick={handleProcessPayment}
            variant="contained"
            disabled={processPaymentMutation.isLoading}
          >
            {processPaymentMutation.isLoading ? (
              <CircularProgress size={20} />
            ) : (
              `Pay $${selectedPlan?.price || 0}`
            )}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default Billing;
