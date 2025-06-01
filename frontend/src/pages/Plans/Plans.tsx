import React, { useState } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Button,
  Grid,
  Chip,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Switch,
  FormControlLabel,
  Alert,
  CircularProgress,
  useTheme,
  alpha,
} from '@mui/material';
import {
  Add as AddIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  Star as StarIcon,
  Check as CheckIcon,
  Business as BusinessIcon,
} from '@mui/icons-material';
import { useQuery, useMutation, useQueryClient } from 'react-query';
import { plansAPI } from '../../services/api';
import toast from 'react-hot-toast';

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
  created_at: string;
  subscription_count?: number;
}

const Plans: React.FC = () => {
  const theme = useTheme();
  const queryClient = useQueryClient();
  const [selectedPlan, setSelectedPlan] = useState<Plan | null>(null);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [dialogType, setDialogType] = useState<'create' | 'edit'>('create');
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    price: 0,
    duration_days: 30,
    max_calls: 0,
    max_minutes: 0,
    features: '',
    is_active: true,
  });

  const { data: plans, isLoading, error } = useQuery('plans', plansAPI.getPlans);

  const createPlanMutation = useMutation(plansAPI.createPlan, {
    onSuccess: () => {
      queryClient.invalidateQueries(['plans']);
      toast.success('Plan created successfully');
      handleCloseDialog();
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to create plan');
    },
  });

  const updatePlanMutation = useMutation(
    ({ id, data }: { id: number; data: any }) => plansAPI.updatePlan(id, data),
    {
      onSuccess: () => {
        queryClient.invalidateQueries(['plans']);
        toast.success('Plan updated successfully');
        handleCloseDialog();
      },
      onError: (error: any) => {
        toast.error(error.response?.data?.detail || 'Failed to update plan');
      },
    }
  );

  const deletePlanMutation = useMutation(plansAPI.deletePlan, {
    onSuccess: () => {
      queryClient.invalidateQueries(['plans']);
      toast.success('Plan deleted successfully');
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to delete plan');
    },
  });

  const handleOpenDialog = (type: 'create' | 'edit', plan?: Plan) => {
    setDialogType(type);
    if (type === 'edit' && plan) {
      setSelectedPlan(plan);
      setFormData({
        name: plan.name,
        description: plan.description,
        price: plan.price,
        duration_days: plan.duration_days,
        max_calls: plan.max_calls,
        max_minutes: plan.max_minutes,
        features: plan.features,
        is_active: plan.is_active,
      });
    } else {
      setSelectedPlan(null);
      setFormData({
        name: '',
        description: '',
        price: 0,
        duration_days: 30,
        max_calls: 0,
        max_minutes: 0,
        features: '',
        is_active: true,
      });
    }
    setDialogOpen(true);
  };

  const handleCloseDialog = () => {
    setDialogOpen(false);
    setSelectedPlan(null);
  };

  const handleSubmit = () => {
    if (dialogType === 'create') {
      createPlanMutation.mutate(formData);
    } else if (selectedPlan) {
      updatePlanMutation.mutate({ id: selectedPlan.id, data: formData });
    }
  };

  const handleDeletePlan = (planId: number) => {
    if (window.confirm('Are you sure you want to delete this plan?')) {
      deletePlanMutation.mutate(planId);
    }
  };

  const formatFeatures = (features: string) => {
    return features.split(',').map(feature => feature.trim()).filter(Boolean);
  };

  if (error) {
    return (
      <Alert severity="error" sx={{ mb: 3 }}>
        Failed to load plans. Please try again.
      </Alert>
    );
  }

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 4 }}>
        <Typography variant="h4" fontWeight="bold">
          Plans Management
        </Typography>
        <Button
          variant="contained"
          startIcon={<AddIcon />}
          onClick={() => handleOpenDialog('create')}
        >
          Create Plan
        </Button>
      </Box>

      {isLoading ? (
        <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}>
          <CircularProgress />
        </Box>
      ) : (
        <Grid container spacing={3}>
          {plans?.map((plan: Plan) => (
            <Grid item xs={12} md={6} lg={4} key={plan.id}>
              <Card
                sx={{
                  height: '100%',
                  display: 'flex',
                  flexDirection: 'column',
                  position: 'relative',
                  border: plan.subscription_count && plan.subscription_count > 10 ? 
                    `2px solid ${theme.palette.primary.main}` : 'none',
                }}
              >
                {plan.subscription_count && plan.subscription_count > 10 && (
                  <Box
                    sx={{
                      position: 'absolute',
                      top: -1,
                      right: 16,
                      backgroundColor: theme.palette.primary.main,
                      color: 'white',
                      px: 2,
                      py: 0.5,
                      borderRadius: '0 0 8px 8px',
                      fontSize: '0.75rem',
                      fontWeight: 'bold',
                      display: 'flex',
                      alignItems: 'center',
                      gap: 0.5,
                    }}
                  >
                    <StarIcon sx={{ fontSize: 16 }} />
                    Popular
                  </Box>
                )}
                
                <CardContent sx={{ flexGrow: 1, p: 3 }}>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 2 }}>
                    <Box>
                      <Typography variant="h5" fontWeight="bold" sx={{ mb: 1 }}>
                        {plan.name}
                      </Typography>
                      <Chip
                        label={plan.is_active ? 'Active' : 'Inactive'}
                        color={plan.is_active ? 'success' : 'default'}
                        size="small"
                      />
                    </Box>
                    <Box sx={{ display: 'flex', gap: 0.5 }}>
                      <IconButton
                        size="small"
                        onClick={() => handleOpenDialog('edit', plan)}
                        sx={{ color: theme.palette.primary.main }}
                      >
                        <EditIcon fontSize="small" />
                      </IconButton>
                      <IconButton
                        size="small"
                        onClick={() => handleDeletePlan(plan.id)}
                        sx={{ color: theme.palette.error.main }}
                      >
                        <DeleteIcon fontSize="small" />
                      </IconButton>
                    </Box>
                  </Box>

                  <Typography color="text.secondary" sx={{ mb: 3 }}>
                    {plan.description}
                  </Typography>

                  <Box sx={{ mb: 3 }}>
                    <Typography variant="h3" fontWeight="bold" color="primary">
                      ${plan.price}
                    </Typography>
                    <Typography color="text.secondary">
                      per {plan.duration_days} days
                    </Typography>
                  </Box>

                  <Box sx={{ mb: 3 }}>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                      <Typography variant="body2" color="text.secondary">
                        Max Calls
                      </Typography>
                      <Typography variant="body2" fontWeight="bold">
                        {plan.max_calls === 0 ? 'Unlimited' : plan.max_calls.toLocaleString()}
                      </Typography>
                    </Box>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                      <Typography variant="body2" color="text.secondary">
                        Max Minutes
                      </Typography>
                      <Typography variant="body2" fontWeight="bold">
                        {plan.max_minutes === 0 ? 'Unlimited' : plan.max_minutes.toLocaleString()}
                      </Typography>
                    </Box>
                    {plan.subscription_count !== undefined && (
                      <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                        <Typography variant="body2" color="text.secondary">
                          Subscribers
                        </Typography>
                        <Typography variant="body2" fontWeight="bold">
                          {plan.subscription_count}
                        </Typography>
                      </Box>
                    )}
                  </Box>

                  {plan.features && (
                    <Box>
                      <Typography variant="body2" fontWeight="bold" sx={{ mb: 1 }}>
                        Features:
                      </Typography>
                      {formatFeatures(plan.features).map((feature, index) => (
                        <Box key={index} sx={{ display: 'flex', alignItems: 'center', mb: 0.5 }}>
                          <CheckIcon sx={{ fontSize: 16, color: theme.palette.success.main, mr: 1 }} />
                          <Typography variant="body2">{feature}</Typography>
                        </Box>
                      ))}
                    </Box>
                  )}
                </CardContent>
              </Card>
            </Grid>
          ))}
        </Grid>
      )}

      {/* Plan Dialog */}
      <Dialog open={dialogOpen} onClose={handleCloseDialog} maxWidth="md" fullWidth>
        <DialogTitle>
          {dialogType === 'create' ? 'Create New Plan' : 'Edit Plan'}
        </DialogTitle>
        <DialogContent>
          <Box sx={{ pt: 2 }}>
            <Grid container spacing={2}>
              <Grid item xs={12} sm={6}>
                <TextField
                  fullWidth
                  label="Plan Name"
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  sx={{ mb: 2 }}
                />
              </Grid>
              <Grid item xs={12} sm={6}>
                <TextField
                  fullWidth
                  label="Price ($)"
                  type="number"
                  value={formData.price}
                  onChange={(e) => setFormData({ ...formData, price: parseFloat(e.target.value) || 0 })}
                  sx={{ mb: 2 }}
                />
              </Grid>
              <Grid item xs={12}>
                <TextField
                  fullWidth
                  label="Description"
                  multiline
                  rows={3}
                  value={formData.description}
                  onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                  sx={{ mb: 2 }}
                />
              </Grid>
              <Grid item xs={12} sm={4}>
                <TextField
                  fullWidth
                  label="Duration (days)"
                  type="number"
                  value={formData.duration_days}
                  onChange={(e) => setFormData({ ...formData, duration_days: parseInt(e.target.value) || 0 })}
                  sx={{ mb: 2 }}
                />
              </Grid>
              <Grid item xs={12} sm={4}>
                <TextField
                  fullWidth
                  label="Max Calls (0 = unlimited)"
                  type="number"
                  value={formData.max_calls}
                  onChange={(e) => setFormData({ ...formData, max_calls: parseInt(e.target.value) || 0 })}
                  sx={{ mb: 2 }}
                />
              </Grid>
              <Grid item xs={12} sm={4}>
                <TextField
                  fullWidth
                  label="Max Minutes (0 = unlimited)"
                  type="number"
                  value={formData.max_minutes}
                  onChange={(e) => setFormData({ ...formData, max_minutes: parseInt(e.target.value) || 0 })}
                  sx={{ mb: 2 }}
                />
              </Grid>
              <Grid item xs={12}>
                <TextField
                  fullWidth
                  label="Features (comma-separated)"
                  multiline
                  rows={2}
                  value={formData.features}
                  onChange={(e) => setFormData({ ...formData, features: e.target.value })}
                  placeholder="24/7 Support, Advanced Analytics, Priority Processing"
                  sx={{ mb: 2 }}
                />
              </Grid>
              <Grid item xs={12}>
                <FormControlLabel
                  control={
                    <Switch
                      checked={formData.is_active}
                      onChange={(e) => setFormData({ ...formData, is_active: e.target.checked })}
                    />
                  }
                  label="Active"
                />
              </Grid>
            </Grid>
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCloseDialog}>Cancel</Button>
          <Button
            onClick={handleSubmit}
            variant="contained"
            disabled={createPlanMutation.isLoading || updatePlanMutation.isLoading}
          >
            {createPlanMutation.isLoading || updatePlanMutation.isLoading ? (
              <CircularProgress size={20} />
            ) : (
              dialogType === 'create' ? 'Create' : 'Update'
            )}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default Plans;
