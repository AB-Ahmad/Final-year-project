import React from 'react';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { createStackNavigator } from '@react-navigation/stack';
import { NavigationContainer } from '@react-navigation/native';
import { Ionicons } from '@expo/vector-icons';

import HomeScreen from './screens/HomeScreen';
import TemplatesScreen from './screens/TemplatesScreen';
import ResultsScreen from './screens/ResultsScreen';
import SettingsScreen from './screens/SettingsScreen';
import GradeScreen from './screens/GradeScreen';
import GradingResultScreen from './screens/GradingResultScreen';

const Tab = createBottomTabNavigator();
const Stack = createStackNavigator();

// Results stack to navigate between Grade → GradingResult
function ResultsStack() {
  return (
    <Stack.Navigator screenOptions={{ headerShown: false }}>
      <Stack.Screen name="ResultsMain" component={ResultsScreen} />
      <Stack.Screen name="Grade" component={GradeScreen} />
      <Stack.Screen name="GradingResult" component={GradingResultScreen} />
    </Stack.Navigator>
  );
}

export default function AppNavigator() {
  return (
    <NavigationContainer>
      <Tab.Navigator
        screenOptions={({ route }) => ({
          tabBarIcon: ({ color, size }) => {
            let iconName;
            if (route.name === 'Home') iconName = 'home-outline';
            else if (route.name === 'Templates') iconName = 'document-text-outline';
            else if (route.name === 'Results') iconName = 'bar-chart-outline';
            else if (route.name === 'Settings') iconName = 'settings-outline';
            return <Ionicons name={iconName} size={size} color={color} />;
          },
          tabBarActiveTintColor: '#3b82f6',
          tabBarInactiveTintColor: 'gray',
          headerShown: false,
        })}
      >
        <Tab.Screen name="Home" component={HomeScreen} />
        <Tab.Screen name="Templates" component={TemplatesScreen} />
        <Tab.Screen name="Results" component={ResultsStack} />
        <Tab.Screen name="Settings" component={SettingsScreen} />
      </Tab.Navigator>
    </NavigationContainer>
  );
}
