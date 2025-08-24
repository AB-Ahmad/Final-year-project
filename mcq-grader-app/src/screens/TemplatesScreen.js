// TemplatesScreen.js
import React, { useState, useEffect } from "react";
import { View, Text, FlatList, TouchableOpacity, StyleSheet, Alert } from "react-native";
import AsyncStorage from "@react-native-async-storage/async-storage";

export default function TemplatesScreen({ navigation }) {
  const [templates, setTemplates] = useState({});

  useEffect(() => {
    const loadTemplates = async () => {
      const stored = await AsyncStorage.getItem("templates");
      if (stored) {
        setTemplates(JSON.parse(stored));
      }
    };
    const unsubscribe = navigation.addListener("focus", loadTemplates);
    return unsubscribe;
  }, [navigation]);

  const handleDelete = async (courseCode) => {
    Alert.alert("Confirm", `Delete template for ${courseCode}?`, [
      { text: "Cancel", style: "cancel" },
      {
        text: "Delete",
        style: "destructive",
        onPress: async () => {
          const updated = { ...templates };
          delete updated[courseCode];
          setTemplates(updated);
          await AsyncStorage.setItem("templates", JSON.stringify(updated));
        },
      },
    ]);
  };

  const handleSelectTemplate = (courseCode, template) => {
    // 👉 Directly go to Grade screen
    navigation.navigate("Grade", { template, courseCode });
  };

  return (
    <View style={styles.container}>
      <Text style={styles.title}>Saved Templates</Text>

      <FlatList
        data={Object.keys(templates)}
        keyExtractor={(item) => item}
        renderItem={({ item }) => (
          <TouchableOpacity
            style={styles.templateCard}
            onPress={() => handleSelectTemplate(item, templates[item])}
            onLongPress={() => handleDelete(item)} // 👉 Long press deletes
          >
            <Text style={styles.course}>{item}</Text>
            <Text style={styles.answers}>
              {templates[item].slice(0, 5).join(", ")} ...
            </Text>
          </TouchableOpacity>
        )}
      />

      {/* Add template button */}
      <TouchableOpacity
        style={styles.addButton}
        onPress={() => navigation.navigate("NewTemplate")}
      >
        <Text style={styles.addButtonText}>+ Create New Template</Text>
      </TouchableOpacity>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, padding: 20, backgroundColor: "white" },
  title: { fontSize: 22, fontWeight: "bold", marginBottom: 20 },
  templateCard: {
    backgroundColor: "#f3f4f6",
    padding: 15,
    borderRadius: 10,
    marginVertical: 8,
  },
  course: { fontSize: 18, fontWeight: "bold" },
  answers: { color: "#666", marginTop: 5 },
  addButton: {
    backgroundColor: "#3b82f6",
    padding: 15,
    borderRadius: 10,
    alignItems: "center",
    marginTop: 20,
  },
  addButtonText: { color: "white", fontWeight: "bold", fontSize: 16 },
});
