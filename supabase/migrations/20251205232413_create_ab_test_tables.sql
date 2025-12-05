/*
  # A/B Test Calculator Database Schema

  ## Overview
  Creates tables for storing A/B test calculations, scenarios, and user data.

  ## New Tables
  
  ### `profiles`
  - `id` (uuid, primary key, references auth.users)
  - `username` (text, unique)
  - `full_name` (text, nullable)
  - `created_at` (timestamptz)
  - `updated_at` (timestamptz)
  
  ### `test_calculations`
  - `id` (uuid, primary key)
  - `user_id` (uuid, references profiles)
  - `name` (text)
  - `baseline_rate` (numeric)
  - `mde` (numeric)
  - `power` (numeric)
  - `significance` (numeric)
  - `test_type` (text)
  - `daily_traffic` (integer)
  - `sample_size_per_variant` (integer)
  - `total_sample_size` (integer)
  - `estimated_days` (integer, nullable)
  - `notes` (text, nullable)
  - `created_at` (timestamptz)
  - `updated_at` (timestamptz)
  
  ### `saved_scenarios`
  - `id` (uuid, primary key)
  - `user_id` (uuid, references profiles)
  - `name` (text)
  - `description` (text, nullable)
  - `scenarios` (jsonb) - array of scenario configurations
  - `created_at` (timestamptz)
  - `updated_at` (timestamptz)
  
  ### `test_templates`
  - `id` (uuid, primary key)
  - `user_id` (uuid, references profiles)
  - `name` (text)
  - `description` (text, nullable)
  - `baseline_rate` (numeric)
  - `mde` (numeric)
  - `power` (numeric)
  - `significance` (numeric)
  - `test_type` (text)
  - `is_public` (boolean)
  - `created_at` (timestamptz)
  - `updated_at` (timestamptz)

  ## Security
  - Enable RLS on all tables
  - Users can only access their own data
  - Public templates are readable by all authenticated users
*/

-- Create profiles table
CREATE TABLE IF NOT EXISTS profiles (
  id uuid PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
  username text UNIQUE NOT NULL,
  full_name text,
  created_at timestamptz DEFAULT now(),
  updated_at timestamptz DEFAULT now()
);

ALTER TABLE profiles ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view own profile"
  ON profiles FOR SELECT
  TO authenticated
  USING (auth.uid() = id);

CREATE POLICY "Users can update own profile"
  ON profiles FOR UPDATE
  TO authenticated
  USING (auth.uid() = id)
  WITH CHECK (auth.uid() = id);

CREATE POLICY "Users can insert own profile"
  ON profiles FOR INSERT
  TO authenticated
  WITH CHECK (auth.uid() = id);

-- Create test_calculations table
CREATE TABLE IF NOT EXISTS test_calculations (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id uuid REFERENCES profiles(id) ON DELETE CASCADE NOT NULL,
  name text NOT NULL,
  baseline_rate numeric NOT NULL,
  mde numeric NOT NULL,
  power numeric NOT NULL,
  significance numeric NOT NULL,
  test_type text NOT NULL,
  daily_traffic integer DEFAULT 0,
  sample_size_per_variant integer NOT NULL,
  total_sample_size integer NOT NULL,
  estimated_days integer,
  notes text,
  created_at timestamptz DEFAULT now(),
  updated_at timestamptz DEFAULT now()
);

ALTER TABLE test_calculations ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view own calculations"
  ON test_calculations FOR SELECT
  TO authenticated
  USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own calculations"
  ON test_calculations FOR INSERT
  TO authenticated
  WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own calculations"
  ON test_calculations FOR UPDATE
  TO authenticated
  USING (auth.uid() = user_id)
  WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can delete own calculations"
  ON test_calculations FOR DELETE
  TO authenticated
  USING (auth.uid() = user_id);

-- Create saved_scenarios table
CREATE TABLE IF NOT EXISTS saved_scenarios (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id uuid REFERENCES profiles(id) ON DELETE CASCADE NOT NULL,
  name text NOT NULL,
  description text,
  scenarios jsonb NOT NULL DEFAULT '[]'::jsonb,
  created_at timestamptz DEFAULT now(),
  updated_at timestamptz DEFAULT now()
);

ALTER TABLE saved_scenarios ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view own scenarios"
  ON saved_scenarios FOR SELECT
  TO authenticated
  USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own scenarios"
  ON saved_scenarios FOR INSERT
  TO authenticated
  WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own scenarios"
  ON saved_scenarios FOR UPDATE
  TO authenticated
  USING (auth.uid() = user_id)
  WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can delete own scenarios"
  ON saved_scenarios FOR DELETE
  TO authenticated
  USING (auth.uid() = user_id);

-- Create test_templates table
CREATE TABLE IF NOT EXISTS test_templates (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id uuid REFERENCES profiles(id) ON DELETE CASCADE NOT NULL,
  name text NOT NULL,
  description text,
  baseline_rate numeric NOT NULL,
  mde numeric NOT NULL,
  power numeric NOT NULL,
  significance numeric NOT NULL,
  test_type text NOT NULL,
  is_public boolean DEFAULT false,
  created_at timestamptz DEFAULT now(),
  updated_at timestamptz DEFAULT now()
);

ALTER TABLE test_templates ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view own templates"
  ON test_templates FOR SELECT
  TO authenticated
  USING (auth.uid() = user_id);

CREATE POLICY "Users can view public templates"
  ON test_templates FOR SELECT
  TO authenticated
  USING (is_public = true);

CREATE POLICY "Users can insert own templates"
  ON test_templates FOR INSERT
  TO authenticated
  WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own templates"
  ON test_templates FOR UPDATE
  TO authenticated
  USING (auth.uid() = user_id)
  WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can delete own templates"
  ON test_templates FOR DELETE
  TO authenticated
  USING (auth.uid() = user_id);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_test_calculations_user_id ON test_calculations(user_id);
CREATE INDEX IF NOT EXISTS idx_test_calculations_created_at ON test_calculations(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_saved_scenarios_user_id ON saved_scenarios(user_id);
CREATE INDEX IF NOT EXISTS idx_test_templates_user_id ON test_templates(user_id);
CREATE INDEX IF NOT EXISTS idx_test_templates_public ON test_templates(is_public) WHERE is_public = true;

-- Create updated_at trigger function
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Add triggers for updated_at
CREATE TRIGGER update_profiles_updated_at BEFORE UPDATE ON profiles
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_test_calculations_updated_at BEFORE UPDATE ON test_calculations
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_saved_scenarios_updated_at BEFORE UPDATE ON saved_scenarios
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_test_templates_updated_at BEFORE UPDATE ON test_templates
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();