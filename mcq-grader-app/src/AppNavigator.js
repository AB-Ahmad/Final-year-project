import React from 'react';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { createStackNavigator } from '@react-navigation/stack';
import { NavigationContainer } from '@react-navigation/native';
import { Ionicons } from '@expo/vector-icons';

import HomeScreen from './screens/HomeScreen';
import TemplatesScreen from './screens/TemplatesScreen';
import NewTemplateScreen from './screens/NewTemplateScreen';
import ResultsScreen from './screens/ResultsScreen';
import GradeScreen from './screens/GradeScreen';
import GradingResultScreen from './screens/GradingResultScreen';
import SettingsScreen from './screens/SettingsScreen';

const Tab = createBottomTabNavigator();
const Stack = createStackNavigator();

// 📌 Stack for Templates tab
function TemplatesStack() {
  return (
    <Stack.Navigator>
      <Stack.Screen 
        name="TemplatesMain" 
        component={TemplatesScreen} 
        options={{ title: "Templates" }} 
      />
      <Stack.Screen 
        name="NewTemplate" 
        component={NewTemplateScreen} 
        options={{ title: "New Template" }} 
      />
      <Stack.Screen 
        name="Grade" 
        component={GradeScreen} 
        options={{ title: "Grade Script" }} 
      />
      <Stack.Screen 
        name="GradingResult" 
        component={GradingResultScreen} 
        options={{ title: "Result" }} 
      />
    </Stack.Navigator>
  );
}

// 📌 Stack for Results tab
function ResultsStack() {
  return (
    <Stack.Navigator>
      <Stack.Screen 
        name="ResultsMain" 
        component={ResultsScreen} 
        options={{ title: "Results" }} 
      />
      <Stack.Screen 
        name="Grade" 
        component={GradeScreen} 
        options={{ title: "Grade Script" }} 
      />
      <Stack.Screen 
        name="GradingResult" 
        component={GradingResultScreen} 
        options={{ title: "Result" }} 
      />
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
        <Tab.Screen name="Templates" component={TemplatesStack} />
        <Tab.Screen name="Results" component={ResultsStack} />
        <Tab.Screen name="Settings" component={SettingsScreen} />
      </Tab.Navigator>
    </NavigationContainer>
  );
}
