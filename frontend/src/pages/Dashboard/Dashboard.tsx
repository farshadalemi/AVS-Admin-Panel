import React, { useState, useEffect } from 'react';
import {
  Box,
  Grid,
  Card,
  CardContent,
  Typography,
  CircularProgress,
  Alert,
  useTheme,
  alpha,
  LinearProgress,
  Chip,
  Avatar,
  List,
  ListItem,
  ListItemAvatar,
  ListItemText,
  Divider,
} from '@mui/material';
import {
  TrendingUp as TrendingUpIcon,
  Phone as PhoneIcon,
  AccessTime as AccessTimeIcon,
  Payment as PaymentIcon,
  People as PeopleIcon,
  Assessment as AssessmentIcon,
  Warning as WarningIcon,
} from '@mui/icons-material';
import { useAuth } from '../../contexts/AuthContext';
import { dashboardAPI } from '../../services/api';
import { useQuery } from 'react-query';

interface DashboardStats {
  total_calls: number;
  total_minutes: number;
  active_subscription: any;
  monthly_usage: any;
  recent_calls: any[];
  usage_percentage: number;
  remaining_calls: number;
  remaining_minutes: number;
}

interface AdminDashboardStats {
  total_users: number;
  active_users: number;
  total_subscriptions: number;
  monthly_revenue: number;
  total_calls: number;
  recent_activity: any[];
  popular_plans: any[];
  expiring_subscriptions: any[];
}

const StatCard: React.FC<{
  title: string;
  value: string | number;
  icon: React.ReactNode;
  color: string;
  subtitle?: string;
  trend?: number;
}> = ({ title, value, icon, color, subtitle, trend }) => {
  const theme = useTheme();
  
  return (
    <Card sx={{ height: '100%' }}>
      <CardContent>
        <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
          <Avatar
            sx={{
              backgroundColor: alpha(color, 0.1),
              color: color,
              mr: 2,
            }}
          >
            {icon}
          </Avatar>
          <Box sx={{ flexGrow: 1 }}>
            <Typography color="text.secondary" variant="body2">
              {title}
            </Typography>
            <Typography variant="h4" fontWeight="bold">
              {value}
            </Typography>
            {subtitle && (
              <Typography variant="body2" color="text.secondary">
                {subtitle}
              </Typography>
            )}
          </Box>
          {trend !== undefined && (
            <Box sx={{ textAlign: 'right' }}>
              <Chip
                label={`${trend > 0 ? '+' : ''}${trend}%`}
                size="small"
                color={trend > 0 ? 'success' : 'error'}
                variant="outlined"
              />
            </Box>
          )}
        </Box>
      </CardContent>
    </Card>
  );
};

const Dashboard: React.FC = () => {
  const theme = useTheme();
  const { user } = useAuth();
  const isAdmin = user?.is_superuser;

  const { data: dashboardData, isLoading, error } = useQuery(
    ['dashboard', isAdmin ? 'admin' : 'user'],
    () => isAdmin ? dashboardAPI.getAdminDashboard() : dashboardAPI.getUserDashboard(),
    {
      refetchInterval: 30000, // Refetch every 30 seconds
    }
  );

  if (isLoading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: 400 }}>
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    return (
      <Alert severity="error" sx={{ mb: 3 }}>
        Failed to load dashboard data. Please try again.
      </Alert>
    );
  }

  if (isAdmin) {
    const adminData = dashboardData as AdminDashboardStats;
    
    return (
      <Box>
        <Typography variant="h4" fontWeight="bold" sx={{ mb: 4 }}>
          Admin Dashboard
        </Typography>

        <Grid container spacing={3} sx={{ mb: 4 }}>
          <Grid item xs={12} sm={6} md={3}>
            <StatCard
              title="Total Users"
              value={adminData?.total_users || 0}
              icon={<PeopleIcon />}
              color={theme.palette.primary.main}
              subtitle={`${adminData?.active_users || 0} active`}
            />
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <StatCard
              title="Active Subscriptions"
              value={adminData?.total_subscriptions || 0}
              icon={<PaymentIcon />}
              color={theme.palette.success.main}
            />
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <StatCard
              title="Monthly Revenue"
              value={`$${adminData?.monthly_revenue || 0}`}
              icon={<TrendingUpIcon />}
              color={theme.palette.warning.main}
            />
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <StatCard
              title="Total Calls"
              value={adminData?.total_calls || 0}
              icon={<PhoneIcon />}
              color={theme.palette.secondary.main}
            />
          </Grid>
        </Grid>

        <Grid container spacing={3}>
          <Grid item xs={12} md={6}>
            <Card>
              <CardContent>
                <Typography variant="h6" fontWeight="bold" sx={{ mb: 2 }}>
                  Recent Activity
                </Typography>
                <List>
                  {adminData?.recent_activity?.slice(0, 5).map((activity: any, index: number) => (
                    <React.Fragment key={index}>
                      <ListItem>
                        <ListItemAvatar>
                          <Avatar sx={{ bgcolor: theme.palette.primary.main }}>
                            <PhoneIcon />
                          </Avatar>
                        </ListItemAvatar>
                        <ListItemText
                          primary={activity.description || 'Activity'}
                          secondary={new Date(activity.created_at).toLocaleString()}
                        />
                      </ListItem>
                      {index < 4 && <Divider />}
                    </React.Fragment>
                  ))}
                </List>
              </CardContent>
            </Card>
          </Grid>
          
          <Grid item xs={12} md={6}>
            <Card>
              <CardContent>
                <Typography variant="h6" fontWeight="bold" sx={{ mb: 2 }}>
                  Expiring Subscriptions
                </Typography>
                <List>
                  {adminData?.expiring_subscriptions?.slice(0, 5).map((subscription: any, index: number) => (
                    <React.Fragment key={index}>
                      <ListItem>
                        <ListItemAvatar>
                          <Avatar sx={{ bgcolor: theme.palette.warning.main }}>
                            <WarningIcon />
                          </Avatar>
                        </ListItemAvatar>
                        <ListItemText
                          primary={subscription.user_email}
                          secondary={`Expires: ${new Date(subscription.end_date).toLocaleDateString()}`}
                        />
                      </ListItem>
                      {index < 4 && <Divider />}
                    </React.Fragment>
                  ))}
                </List>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      </Box>
    );
  }

  // User Dashboard
  const userData = dashboardData as DashboardStats;
  
  return (
    <Box>
      <Typography variant="h4" fontWeight="bold" sx={{ mb: 4 }}>
        Welcome back, {user?.full_name}!
      </Typography>

      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="Total Calls"
            value={userData?.total_calls || 0}
            icon={<PhoneIcon />}
            color={theme.palette.primary.main}
            subtitle="This month"
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="Total Minutes"
            value={userData?.total_minutes || 0}
            icon={<AccessTimeIcon />}
            color={theme.palette.success.main}
            subtitle="This month"
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="Remaining Calls"
            value={userData?.remaining_calls || 0}
            icon={<AssessmentIcon />}
            color={theme.palette.warning.main}
            subtitle="This period"
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="Usage"
            value={`${userData?.usage_percentage || 0}%`}
            icon={<TrendingUpIcon />}
            color={theme.palette.secondary.main}
            subtitle="Of plan limit"
          />
        </Grid>
      </Grid>

      {userData?.active_subscription && (
        <Card sx={{ mb: 3 }}>
          <CardContent>
            <Typography variant="h6" fontWeight="bold" sx={{ mb: 2 }}>
              Current Subscription
            </Typography>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
              <Typography variant="body1">
                {userData.active_subscription.plan_name}
              </Typography>
              <Chip
                label={userData.active_subscription.status}
                color="success"
                variant="outlined"
              />
            </Box>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
              Expires: {new Date(userData.active_subscription.end_date).toLocaleDateString()}
            </Typography>
            <LinearProgress
              variant="determinate"
              value={userData?.usage_percentage || 0}
              sx={{ height: 8, borderRadius: 4 }}
            />
            <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
              {userData?.usage_percentage || 0}% of plan limit used
            </Typography>
          </CardContent>
        </Card>
      )}

      <Card>
        <CardContent>
          <Typography variant="h6" fontWeight="bold" sx={{ mb: 2 }}>
            Recent Calls
          </Typography>
          <List>
            {userData?.recent_calls?.slice(0, 5).map((call: any, index: number) => (
              <React.Fragment key={index}>
                <ListItem>
                  <ListItemAvatar>
                    <Avatar sx={{ bgcolor: theme.palette.primary.main }}>
                      <PhoneIcon />
                    </Avatar>
                  </ListItemAvatar>
                  <ListItemText
                    primary={`${call.caller_number} → ${call.destination_number}`}
                    secondary={`${call.duration || 0}s • ${new Date(call.start_time).toLocaleString()}`}
                  />
                  <Chip
                    label={call.status}
                    size="small"
                    color={call.status === 'completed' ? 'success' : 'default'}
                    variant="outlined"
                  />
                </ListItem>
                {index < 4 && <Divider />}
              </React.Fragment>
            ))}
          </List>
        </CardContent>
      </Card>
    </Box>
  );
};

export default Dashboard;
